"""Repair and constrain customer payment and sale-return integrity.

Revision ID: b2e4f8a1c3d5
Revises: b1c27a4e6f0

PostgreSQL runs this migration inside Alembic's migration transaction. The
table locks, guarded repairs, post-repair checks, and constraint DDL therefore
succeed or roll back together.
"""

from alembic import op


revision = "b2e4f8a1c3d5"
down_revision = "b1c27a4e6f0"
branch_labels = None
depends_on = None


PAYMENTS_AMOUNT_CHECK = "ck_payments_amount_positive_finite"
SALES_CUSTOMER_UNIQUE = "uq_sales_id_customer_id"
SALE_RETURNS_CUSTOMER_FOREIGN_KEY = "fk_sale_returns_sale_customer"


LOCK_SQL = """
LOCK TABLE public.payments, public.sale_returns, public.sales
IN ACCESS EXCLUSIVE MODE
"""


REPAIR_SQL = """
DO $financial_integrity$
DECLARE
    zero_payment_count bigint;
    invalid_nonzero_payment_count bigint;
    approved_customer_mismatch_count bigint;
    other_customer_mismatch_count bigint;
    affected_row_count bigint;
    remaining_violation_count bigint;
BEGIN
    SELECT count(*)
    INTO zero_payment_count
    FROM public.payments
    WHERE amount = 0;

    SELECT count(*)
    INTO invalid_nonzero_payment_count
    FROM public.payments
    WHERE (
        amount < 0
        AND amount::text NOT IN ('NaN', 'Infinity', '-Infinity')
    )
    OR amount::text IN ('NaN', 'Infinity', '-Infinity');

    SELECT count(*)
    INTO approved_customer_mismatch_count
    FROM public.sale_returns AS sale_return
    JOIN public.sales AS sale ON sale.id = sale_return.sale_id
    WHERE sale_return.status = 'Completed'
      AND sale_return.customer_id IS NOT NULL
      AND sale.customer_id IS NOT NULL
      AND sale_return.customer_id IS DISTINCT FROM sale.customer_id;

    SELECT count(*)
    INTO other_customer_mismatch_count
    FROM public.sale_returns AS sale_return
    LEFT JOIN public.sales AS sale ON sale.id = sale_return.sale_id
    WHERE (
        sale.id IS NULL
        OR sale_return.customer_id IS DISTINCT FROM sale.customer_id
    )
      AND NOT (
          sale.id IS NOT NULL
          AND sale_return.status = 'Completed'
          AND sale_return.customer_id IS NOT NULL
          AND sale.customer_id IS NOT NULL
          AND sale_return.customer_id IS DISTINCT FROM sale.customer_id
      );

    IF invalid_nonzero_payment_count <> 0 THEN
        RAISE EXCEPTION
            'Financial integrity preflight failed: invalid nonzero payment.';
    END IF;

    IF other_customer_mismatch_count <> 0 THEN
        RAISE EXCEPTION
            'Financial integrity preflight failed: unexpected sale-return mismatch.';
    END IF;

    IF NOT (
        (
            zero_payment_count = 1
            AND approved_customer_mismatch_count = 1
        )
        OR (
            zero_payment_count = 0
            AND approved_customer_mismatch_count = 0
        )
    ) THEN
        RAISE EXCEPTION
            'Financial integrity preflight failed: unexpected repair count pair.';
    END IF;

    DELETE FROM public.payments
    WHERE amount = 0;

    GET DIAGNOSTICS affected_row_count = ROW_COUNT;
    IF affected_row_count <> zero_payment_count THEN
        RAISE EXCEPTION
            'Financial integrity repair failed: zero-payment row count changed.';
    END IF;

    UPDATE public.sale_returns AS sale_return
    SET customer_id = sale.customer_id
    FROM public.sales AS sale
    WHERE sale.id = sale_return.sale_id
      AND sale_return.status = 'Completed'
      AND sale_return.customer_id IS NOT NULL
      AND sale.customer_id IS NOT NULL
      AND sale_return.customer_id IS DISTINCT FROM sale.customer_id;

    GET DIAGNOSTICS affected_row_count = ROW_COUNT;
    IF affected_row_count <> approved_customer_mismatch_count THEN
        RAISE EXCEPTION
            'Financial integrity repair failed: sale-return row count changed.';
    END IF;

    SELECT count(*)
    INTO remaining_violation_count
    FROM public.payments
    WHERE amount <= 0
       OR amount::text IN ('NaN', 'Infinity', '-Infinity');

    IF remaining_violation_count <> 0 THEN
        RAISE EXCEPTION
            'Financial integrity repair failed: invalid payments remain.';
    END IF;

    SELECT count(*)
    INTO remaining_violation_count
    FROM public.sale_returns AS sale_return
    LEFT JOIN public.sales AS sale ON sale.id = sale_return.sale_id
    WHERE sale.id IS NULL
       OR sale_return.customer_id IS DISTINCT FROM sale.customer_id;

    IF remaining_violation_count <> 0 THEN
        RAISE EXCEPTION
            'Financial integrity repair failed: sale-return mismatches remain.';
    END IF;
END;
$financial_integrity$
"""


ADD_PAYMENTS_CHECK_SQL = f"""
ALTER TABLE public.payments
ADD CONSTRAINT {PAYMENTS_AMOUNT_CHECK}
CHECK (
    amount > 0
    AND amount::text NOT IN ('NaN', 'Infinity', '-Infinity')
) NOT VALID
"""

VALIDATE_PAYMENTS_CHECK_SQL = f"""
ALTER TABLE public.payments
VALIDATE CONSTRAINT {PAYMENTS_AMOUNT_CHECK}
"""

ADD_SALES_CUSTOMER_UNIQUE_SQL = f"""
ALTER TABLE public.sales
ADD CONSTRAINT {SALES_CUSTOMER_UNIQUE}
UNIQUE (id, customer_id)
"""

ADD_SALE_RETURNS_CUSTOMER_FOREIGN_KEY_SQL = f"""
ALTER TABLE public.sale_returns
ADD CONSTRAINT {SALE_RETURNS_CUSTOMER_FOREIGN_KEY}
FOREIGN KEY (sale_id, customer_id)
REFERENCES public.sales (id, customer_id)
MATCH SIMPLE
ON UPDATE NO ACTION
ON DELETE CASCADE
NOT VALID
"""

VALIDATE_SALE_RETURNS_CUSTOMER_FOREIGN_KEY_SQL = f"""
ALTER TABLE public.sale_returns
VALIDATE CONSTRAINT {SALE_RETURNS_CUSTOMER_FOREIGN_KEY}
"""


def upgrade() -> None:
    op.execute(LOCK_SQL)
    op.execute(REPAIR_SQL)
    op.execute(ADD_PAYMENTS_CHECK_SQL)
    op.execute(VALIDATE_PAYMENTS_CHECK_SQL)
    op.execute(ADD_SALES_CUSTOMER_UNIQUE_SQL)
    op.execute(ADD_SALE_RETURNS_CUSTOMER_FOREIGN_KEY_SQL)
    op.execute(VALIDATE_SALE_RETURNS_CUSTOMER_FOREIGN_KEY_SQL)


def downgrade() -> None:
    raise RuntimeError(
        "Financial-integrity hardening downgrade is intentionally unsupported "
        "because the approved historical repairs cannot be reconstructed safely."
    )
