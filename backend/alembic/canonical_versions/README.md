# Canonical Alembic revisions

This directory is the only active Alembic version location. It begins with a
new canonical root generated from the reviewed `bhavani_erp_v2` live-schema
contract.

The five files under `alembic/versions` are retired pre-canonical history. They
remain byte-for-byte intact for investigation and are intentionally excluded
from `version_locations`. Their last retired head is `ce97b6c5d53e`, and the
source commit immediately before the rebaseline is `524f768`.

Existing databases require a separately reviewed manual stamp after an empty
database rehearsal and exact schema comparison. Never run this root migration
against `bhavani_erp_v2`. No live stamp is part of this change.

The live database currently has ten redundant indexes on primary-key columns.
They are allowed legacy extras and are omitted from the canonical root:

- `ix_brands_id`
- `ix_categories_id`
- `ix_customers_id`
- `ix_product_variants_id`
- `ix_products_id`
- `ix_sale_items_id`
- `ix_sales_id`
- `ix_shops_id`
- `ix_stocks_id`
- `ix_users_id`

Any later removal of those live indexes belongs in a separately reviewed
cleanup migration.

## Financial-integrity hardening rehearsal

Revision `b2e4f8a1c3d5` repairs the approved historical payment and Sale Return
invariants, then adds the related constraints. Its composite foreign key uses
PostgreSQL `MATCH SIMPLE`: a null `sale_returns.customer_id` is not checked by
that composite key. The application must therefore retain its null-safe
customer equality validation, including the legitimate both-null case.
The existing single-column Sale foreign key and the composite Sale/customer
foreign key both use `ON DELETE CASCADE` so their delete actions are compatible.
The known historical state has one zero-value Payment and one approved completed
Sale Return customer mismatch, so it repairs exactly one row for each predicate.
A clean or freshly built database has neither violation, performs zero historical
repairs, and proceeds to the same constraint DDL. Mixed counts, counts above one,
or any other mismatch category abort the migration before either repair runs.

Rehearse this revision only on a separately provisioned disposable clone that
contains the approved pre-repair history and is already stamped at
`b1c27a4e6f0`. Never use `bhavani_erp_v2`, its recovery copy, or a prior
baseline-rehearsal database for this procedure.

In PowerShell, configure `DATABASE_URL` through the normal secure environment
mechanism so it names the new disposable database; do not put credentials in a
command history or repository file. Then run:

```powershell
& ".\venv\Scripts\python.exe" -m alembic current
& ".\venv\Scripts\python.exe" -m alembic upgrade b2e4f8a1c3d5
& ".\venv\Scripts\python.exe" -m alembic current
```

Before upgrade, require `current_database()` to equal the disposable database,
`transaction_read_only` to be `off`, and the sole Alembic revision to be
`b1c27a4e6f0`. After upgrade, require revision `b2e4f8a1c3d5`, zero violations
for the repaired predicates, and exact presence and validation of:

- `ck_payments_amount_positive_finite`
- `uq_sales_id_customer_id`
- `fk_sale_returns_sale_customer`

Also verify that rejected payment inserts and mismatched non-null Sale Return
inserts fail inside transactions that are rolled back. Preserve the rehearsal
logs, compare aggregate row counts before and after, and discard the disposable
database if any assertion differs. Downgrade is intentionally unavailable
because it cannot reconstruct the deleted or corrected historical rows.
