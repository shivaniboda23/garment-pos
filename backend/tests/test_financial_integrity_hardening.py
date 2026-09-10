import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest import mock

from alembic.config import Config
from alembic.script import ScriptDirectory


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
MIGRATION_PATH = (
    BACKEND_ROOT
    / "alembic"
    / "canonical_versions"
    / "b2e4f8a1c3d5_financial_integrity_hardening.py"
)
CUSTOMER_PAYMENT_PATH = BACKEND_ROOT / "app" / "crud" / "customer_payment.py"
SALE_RETURN_PATH = BACKEND_ROOT / "app" / "crud" / "sale_return.py"
CANONICAL_README = (
    BACKEND_ROOT / "alembic" / "canonical_versions" / "README.md"
)

REVISION = "b2e4f8a1c3d5"
DOWN_REVISION = "b1c27a4e6f0"
PAYMENTS_CHECK = "ck_payments_amount_positive_finite"
SALES_CUSTOMER_UNIQUE = "uq_sales_id_customer_id"
SALE_RETURNS_CUSTOMER_FK = "fk_sale_returns_sale_customer"


MODEL_METADATA_SCRIPT = r"""
import json
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from app.models.payment import Payment
from app.models.sale import Sale
from app.models.sale_return import SaleReturn

payment_checks = [
    {
        "name": constraint.name,
        "expression": str(constraint.sqltext),
    }
    for constraint in Payment.__table__.constraints
    if isinstance(constraint, CheckConstraint)
]
sale_uniques = [
    {
        "name": constraint.name,
        "columns": [column.name for column in constraint.columns],
    }
    for constraint in Sale.__table__.constraints
    if isinstance(constraint, UniqueConstraint)
]
sale_return_foreign_keys = [
    {
        "name": constraint.name,
        "columns": [column.name for column in constraint.columns],
        "targets": [element.target_fullname for element in constraint.elements],
        "ondelete": constraint.elements[0].ondelete,
        "onupdate": constraint.elements[0].onupdate,
        "match": constraint.elements[0].match,
    }
    for constraint in SaleReturn.__table__.constraints
    if isinstance(constraint, ForeignKeyConstraint)
]
print(json.dumps({
    "payment_checks": payment_checks,
    "sale_uniques": sale_uniques,
    "sale_return_foreign_keys": sale_return_foreign_keys,
}, sort_keys=True))
"""


APPLICATION_VALIDATION_SCRIPT = r"""
import json
from decimal import Decimal
import sys
from types import SimpleNamespace
import types

try:
    from fastapi import HTTPException
except ModuleNotFoundError:
    fastapi = types.ModuleType("fastapi")
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail
    fastapi.HTTPException = HTTPException
    sys.modules["fastapi"] = fastapi

from app.crud.customer_payment import (
    _validated_payment_amount,
    create_customer_payment,
)
from app.crud.sale_return import _validate_sale_return_customer

class NoDatabaseAccess:
    def __getattr__(self, name):
        raise AssertionError(f"database accessed through {name}")

invalid_results = {}
for value in ("0", "-0.01", "NaN", "Infinity", "-Infinity"):
    try:
        create_customer_payment(
            db=NoDatabaseAccess(),
            shop_id=1,
            data=SimpleNamespace(amount=value),
        )
    except HTTPException as exc:
        invalid_results[value] = exc.status_code

customer_results = {}
for name, sale_customer, requested_customer in (
    ("matching", 7, 7),
    ("different", 7, 8),
    ("both_null", None, None),
    ("one_null", 7, None),
):
    try:
        _validate_sale_return_customer(sale_customer, requested_customer)
    except HTTPException as exc:
        customer_results[name] = exc.status_code
    else:
        customer_results[name] = "accepted"

print(json.dumps({
    "invalid_results": invalid_results,
    "positive_amount": str(_validated_payment_amount(Decimal("1.00"))),
    "customer_results": customer_results,
}, sort_keys=True))
"""


def _load_migration():
    spec = importlib.util.spec_from_file_location("financial_integrity", MIGRATION_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load migration: {MIGRATION_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_database_free_subprocess(script):
    environment = os.environ.copy()
    environment["DATABASE_URL"] = "sqlite:///:memory:"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class FinancialIntegrityMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.migration = _load_migration()
        cls.source = MIGRATION_PATH.read_text(encoding="utf-8")

    def test_revision_is_the_only_head_after_canonical_root(self):
        scripts = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
        revisions = {item.revision: item for item in scripts.walk_revisions()}
        self.assertEqual({DOWN_REVISION, REVISION}, set(revisions))
        self.assertEqual([DOWN_REVISION], scripts.get_bases())
        self.assertEqual([REVISION], scripts.get_heads())
        self.assertEqual(DOWN_REVISION, revisions[REVISION].down_revision)

    def test_migration_contains_no_hardcoded_record_or_private_data(self):
        self.assertIsNone(re.search(r"\bid\s*=\s*\d+\b", self.source))
        for forbidden in (
            "customer_name",
            "phone",
            "transaction_reference",
            "reference_number",
            "invoice_number",
        ):
            self.assertNotIn(forbidden, self.source)

    def test_preflight_uses_exact_approved_invariant_categories(self):
        sql = self.migration.REPAIR_SQL
        required = (
            "WHERE amount = 0",
            "amount < 0",
            "amount::text NOT IN ('NaN', 'Infinity', '-Infinity')",
            "invalid_nonzero_payment_count <> 0",
            "sale_return.status = 'Completed'",
            "sale_return.customer_id IS NOT NULL",
            "sale.customer_id IS NOT NULL",
            "sale_return.customer_id IS DISTINCT FROM sale.customer_id",
            "other_customer_mismatch_count <> 0",
        )
        for fragment in required:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, sql)

    def test_preflight_accepts_exactly_historical_or_clean_count_pairs(self):
        sql = self.migration.REPAIR_SQL
        guard = re.search(
            r"IF NOT \(\s*(.*?)\s*\) THEN\s*RAISE EXCEPTION\s*"
            r"'Financial integrity preflight failed: unexpected repair count pair\.';",
            sql,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(guard)
        accepted_pairs = {
            (int(payment_count), int(mismatch_count))
            for payment_count, mismatch_count in re.findall(
                r"zero_payment_count = (\d+)\s+"
                r"AND approved_customer_mismatch_count = (\d+)",
                guard.group(1),
            )
        }
        self.assertEqual({(1, 1), (0, 0)}, accepted_pairs)

        for accepted in ((1, 1), (0, 0)):
            with self.subTest(accepted=accepted):
                self.assertIn(accepted, accepted_pairs)
        for rejected in ((1, 0), (0, 1), (2, 2), (2, 1), (1, 2), (2, 0), (0, 2)):
            with self.subTest(rejected=rejected):
                self.assertNotIn(rejected, accepted_pairs)

    def test_repair_is_predicate_based_and_asserts_affected_counts(self):
        sql = self.migration.REPAIR_SQL
        self.assertIn("DELETE FROM public.payments\n    WHERE amount = 0", sql)
        self.assertIn("UPDATE public.sale_returns AS sale_return", sql)
        self.assertIn("SET customer_id = sale.customer_id", sql)
        self.assertEqual(2, sql.count("GET DIAGNOSTICS affected_row_count = ROW_COUNT"))
        self.assertEqual(0, sql.count("IF affected_row_count <> 1"))
        self.assertIn("IF affected_row_count <> zero_payment_count", sql)
        self.assertIn(
            "IF affected_row_count <> approved_customer_mismatch_count",
            sql,
        )
        self.assertIn("END;\n$financial_integrity$", sql)

    def test_historical_repair_predicates_remain_exact(self):
        sql = self.migration.REPAIR_SQL
        self.assertIn(
            """DELETE FROM public.payments
    WHERE amount = 0;""",
            sql,
        )
        self.assertIn(
            """UPDATE public.sale_returns AS sale_return
    SET customer_id = sale.customer_id
    FROM public.sales AS sale
    WHERE sale.id = sale_return.sale_id
      AND sale_return.status = 'Completed'
      AND sale_return.customer_id IS NOT NULL
      AND sale.customer_id IS NOT NULL
      AND sale_return.customer_id IS DISTINCT FROM sale.customer_id;""",
            sql,
        )

    def test_post_repair_rechecks_require_zero_violations(self):
        sql = self.migration.REPAIR_SQL
        self.assertIn("WHERE amount <= 0", sql)
        self.assertIn("sale.id IS NULL", sql)
        self.assertGreaterEqual(sql.count("remaining_violation_count <> 0"), 2)

    def test_upgrade_operation_order_and_constraint_ddl(self):
        with mock.patch.object(self.migration.op, "execute") as execute:
            self.migration.upgrade()

        statements = [call.args[0] for call in execute.call_args_list]
        self.assertEqual(
            [
                self.migration.LOCK_SQL,
                self.migration.REPAIR_SQL,
                self.migration.ADD_PAYMENTS_CHECK_SQL,
                self.migration.VALIDATE_PAYMENTS_CHECK_SQL,
                self.migration.ADD_SALES_CUSTOMER_UNIQUE_SQL,
                self.migration.ADD_SALE_RETURNS_CUSTOMER_FOREIGN_KEY_SQL,
                self.migration.VALIDATE_SALE_RETURNS_CUSTOMER_FOREIGN_KEY_SQL,
            ],
            statements,
        )
        self.assertIn(
            "LOCK TABLE public.payments, public.sale_returns, public.sales",
            statements[0],
        )
        self.assertIn("ACCESS EXCLUSIVE", statements[0])
        self.assertIn("ALTER TABLE public.payments", statements[2])
        self.assertIn("CHECK (", statements[2])
        self.assertIn("amount > 0", statements[2])
        self.assertIn("NOT VALID", statements[2])
        self.assertIn(f"VALIDATE CONSTRAINT {PAYMENTS_CHECK}", statements[3])
        self.assertIn("UNIQUE (id, customer_id)", statements[4])
        self.assertIn("FOREIGN KEY (sale_id, customer_id)", statements[5])
        self.assertIn("MATCH SIMPLE", statements[5])
        self.assertIn("ON UPDATE NO ACTION", statements[5])
        self.assertIn("REFERENCES public.sales (id, customer_id)", statements[5])
        self.assertIn("ON DELETE CASCADE", statements[5])
        self.assertIn("NOT VALID", statements[5])
        self.assertIn(
            f"VALIDATE CONSTRAINT {SALE_RETURNS_CUSTOMER_FK}",
            statements[6],
        )

    def test_every_affected_relation_reference_is_public_qualified(self):
        executable_sql = "\n".join(
            (
                self.migration.LOCK_SQL,
                self.migration.REPAIR_SQL,
                self.migration.ADD_PAYMENTS_CHECK_SQL,
                self.migration.VALIDATE_PAYMENTS_CHECK_SQL,
                self.migration.ADD_SALES_CUSTOMER_UNIQUE_SQL,
                self.migration.ADD_SALE_RETURNS_CUSTOMER_FOREIGN_KEY_SQL,
                self.migration.VALIDATE_SALE_RETURNS_CUSTOMER_FOREIGN_KEY_SQL,
            )
        )
        unqualified_relation = re.compile(
            r"\b(?:FROM|JOIN|UPDATE|DELETE\s+FROM|ALTER\s+TABLE|REFERENCES)\s+"
            r"(?:payments|sale_returns|sales)\b",
            flags=re.IGNORECASE,
        )
        self.assertIsNone(unqualified_relation.search(executable_sql))
        self.assertIn(
            "LOCK TABLE public.payments, public.sale_returns, public.sales",
            executable_sql,
        )

    def test_constraint_names_are_exact(self):
        self.assertEqual(PAYMENTS_CHECK, self.migration.PAYMENTS_AMOUNT_CHECK)
        self.assertEqual(SALES_CUSTOMER_UNIQUE, self.migration.SALES_CUSTOMER_UNIQUE)
        self.assertEqual(
            SALE_RETURNS_CUSTOMER_FK,
            self.migration.SALE_RETURNS_CUSTOMER_FOREIGN_KEY,
        )

    def test_migration_relies_on_alembic_transaction_without_transaction_control(self):
        statements = (
            self.migration.LOCK_SQL,
            self.migration.REPAIR_SQL,
            self.migration.ADD_PAYMENTS_CHECK_SQL,
            self.migration.VALIDATE_PAYMENTS_CHECK_SQL,
            self.migration.ADD_SALES_CUSTOMER_UNIQUE_SQL,
            self.migration.ADD_SALE_RETURNS_CUSTOMER_FOREIGN_KEY_SQL,
            self.migration.VALIDATE_SALE_RETURNS_CUSTOMER_FOREIGN_KEY_SQL,
        )
        for statement in statements:
            with self.subTest(statement=statement.splitlines()[1]):
                self.assertNotRegex(statement, r"(?im)^\s*COMMIT\b")
                self.assertFalse(statement.lstrip().upper().startswith("BEGIN"))

    def test_downgrade_fails_before_any_alembic_operation(self):
        with mock.patch.object(self.migration.op, "execute") as execute:
            with self.assertRaisesRegex(RuntimeError, "intentionally unsupported"):
                self.migration.downgrade()
        execute.assert_not_called()

    def test_readme_documents_disposable_rehearsal_and_match_simple(self):
        readme = CANONICAL_README.read_text(encoding="utf-8")
        for required in (
            "MATCH SIMPLE",
            "ON DELETE CASCADE",
            "performs zero historical\nrepairs",
            "Mixed counts, counts above one",
            "legitimate both-null case",
            "separately provisioned disposable clone",
            "Never use `bhavani_erp_v2`",
            "alembic upgrade b2e4f8a1c3d5",
            PAYMENTS_CHECK,
            SALES_CUSTOMER_UNIQUE,
            SALE_RETURNS_CUSTOMER_FK,
            "transactions that are rolled back",
        ):
            with self.subTest(required=required):
                self.assertIn(required, readme)


class FinancialIntegrityModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata = _run_database_free_subprocess(MODEL_METADATA_SCRIPT)

    def test_payment_check_metadata(self):
        self.assertEqual(
            [
                {
                    "name": PAYMENTS_CHECK,
                    "expression": (
                        "amount > 0 AND amount::text NOT IN "
                        "('NaN', 'Infinity', '-Infinity')"
                    ),
                }
            ],
            self.metadata["payment_checks"],
        )

    def test_sales_parent_unique_metadata(self):
        self.assertEqual(2, len(self.metadata["sale_uniques"]))
        matching = [
            constraint
            for constraint in self.metadata["sale_uniques"]
            if constraint["name"] == SALES_CUSTOMER_UNIQUE
        ]
        self.assertEqual(
            [{"name": SALES_CUSTOMER_UNIQUE, "columns": ["id", "customer_id"]}],
            matching,
        )

    def test_sale_return_composite_and_single_column_foreign_keys(self):
        constraints = self.metadata["sale_return_foreign_keys"]
        self.assertEqual(4, len(constraints))
        composite = [
            constraint
            for constraint in constraints
            if constraint["name"] == SALE_RETURNS_CUSTOMER_FK
        ]
        self.assertEqual(
            [
                {
                    "name": SALE_RETURNS_CUSTOMER_FK,
                    "columns": ["sale_id", "customer_id"],
                    "targets": ["sales.id", "sales.customer_id"],
                    "ondelete": "CASCADE",
                    "onupdate": "NO ACTION",
                    "match": "SIMPLE",
                }
            ],
            composite,
        )
        single_targets = {
            tuple(constraint["columns"]): tuple(constraint["targets"])
            for constraint in constraints
            if constraint["name"] is None and len(constraint["columns"]) == 1
        }
        self.assertEqual(("sales.id",), single_targets[("sale_id",)])
        self.assertEqual(("customers.id",), single_targets[("customer_id",)])
        self.assertEqual(("shops.id",), single_targets[("shop_id",)])

    def test_sale_foreign_keys_have_compatible_delete_semantics(self):
        sale_constraints = [
            constraint
            for constraint in self.metadata["sale_return_foreign_keys"]
            if "sale_id" in constraint["columns"]
        ]
        self.assertEqual(2, len(sale_constraints))
        self.assertEqual(
            {"CASCADE"},
            {constraint["ondelete"] for constraint in sale_constraints},
        )


class FinancialIntegrityApplicationValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = _run_database_free_subprocess(APPLICATION_VALIDATION_SCRIPT)

    def test_invalid_customer_payments_are_rejected_before_database_access(self):
        self.assertEqual(
            {
                "0": 400,
                "-0.01": 400,
                "NaN": 400,
                "Infinity": 400,
                "-Infinity": 400,
            },
            self.results["invalid_results"],
        )
        self.assertEqual("1.00", self.results["positive_amount"])

    def test_sale_return_customer_validation_is_null_safe(self):
        self.assertEqual(
            {
                "matching": "accepted",
                "different": 400,
                "both_null": "accepted",
                "one_null": 400,
            },
            self.results["customer_results"],
        )

    def test_creation_path_copies_the_sale_customer(self):
        source = SALE_RETURN_PATH.read_text(encoding="utf-8")
        self.assertRegex(source, r"customer_id\s*=\s*sale\.customer_id")
        self.assertIn("_validate_sale_return_customer(", source)

    def test_payment_validation_precedes_bill_query(self):
        source = CUSTOMER_PAYMENT_PATH.read_text(encoding="utf-8")
        function = source[source.index("def create_customer_payment(") :]
        self.assertLess(
            function.index("_validated_payment_amount(data.amount)"),
            function.index("db.query(Bill)"),
        )


if __name__ == "__main__":
    unittest.main()
