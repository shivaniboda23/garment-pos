import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = (
    "bill_items",
    "bills",
    "brands",
    "categories",
    "customers",
    "expense_categories",
    "expenses",
    "payments",
    "product_variants",
    "products",
    "purchase_items",
    "purchase_return_items",
    "purchase_returns",
    "purchases",
    "sale_items",
    "sale_return_items",
    "sale_returns",
    "sales",
    "shops",
    "stock_movements",
    "stocks",
    "supplier_credit_applications",
    "supplier_payments",
    "suppliers",
    "tailor_payments",
    "tailoring_jobs",
    "users",
)

REGISTERED_MODELS_SCRIPT = """
import json

from app.db.database import Base
import app.models

print(json.dumps(sorted(Base.metadata.tables)))
"""

ALL_MODEL_MODULES_SCRIPT = """
import importlib
import json
import pkgutil

from app.db.database import Base
import app.models as models_package

for module_info in pkgutil.iter_modules(models_package.__path__):
    if module_info.name == "__init__":
        continue
    importlib.import_module(
        f"{models_package.__name__}.{module_info.name}"
    )

print(json.dumps(sorted(Base.metadata.tables)))
"""


def _load_tables_from_clean_subprocess(script):
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

    return tuple(json.loads(result.stdout))


class ModelRegistryTests(unittest.TestCase):
    def assert_table_sets_equal(self, actual, expected):
        actual_set = set(actual)
        expected_set = set(expected)
        missing = sorted(expected_set - actual_set)
        extra = sorted(actual_set - expected_set)

        self.assertEqual(
            actual,
            expected,
            msg=(
                f"Model registry differs: missing={missing}, "
                f"extra={extra}"
            ),
        )

    def test_app_models_registers_exact_expected_tables(self):
        registered_tables = _load_tables_from_clean_subprocess(
            REGISTERED_MODELS_SCRIPT
        )

        self.assert_table_sets_equal(
            registered_tables,
            EXPECTED_TABLES,
        )

    def test_app_models_matches_all_model_modules(self):
        registered_tables = _load_tables_from_clean_subprocess(
            REGISTERED_MODELS_SCRIPT
        )
        complete_tables = _load_tables_from_clean_subprocess(
            ALL_MODEL_MODULES_SCRIPT
        )

        self.assert_table_sets_equal(
            registered_tables,
            complete_tables,
        )


if __name__ == "__main__":
    unittest.main()
