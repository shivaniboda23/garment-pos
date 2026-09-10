import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest import mock

from alembic.config import Config
from alembic.script import ScriptDirectory
import sqlalchemy as sa

from scripts.compare_postgres_schema_contracts import (
    ALLOWED_REDUNDANT_INDEXES,
    TAILORING_STOCK_TYPE_CHECK_EXPRESSIONS,
    compare_contracts,
)


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
ALEMBIC_ROOT = BACKEND_ROOT / "alembic"
CANONICAL_VERSIONS = ALEMBIC_ROOT / "canonical_versions"
HISTORICAL_VERSIONS = ALEMBIC_ROOT / "versions"
CONTRACT_PATH = (
    BACKEND_ROOT / "schema_contract" / "bhavani_erp_v2_live_schema.json"
)

HISTORICAL_MIGRATION_HASHES = {
    "4f15d0df1fe5_add_customers_table.py": (
        "7A077BCE114E13760501001502F62C823242EE2EC992BEA267B4A6339FC0F539"
    ),
    "954c96a7787d_initial_erp_schema.py": (
        "CFB766AC26720ED5225B8F6B2077DFC7B4FEC6ED143CF8D18BCFC84A57953F99"
    ),
    "b7724ffda64d_add_product_variants.py": (
        "F5CDABE4EBB64B9FC0213DC51E84E3F90C03B6213D3EAA09C50C1FE0AB564A83"
    ),
    "ce97b6c5d53e_add_sales_tables.py": (
        "C4C57482C1867493C00B17380FFDDC1749C73844B12822AAA3816D31E96018DD"
    ),
    "d4ef676f2abd_add_product_inventory.py": (
        "2B4CAA16697F85DA785E0FA0993310857CBA298B952FB9B9A62DF636C89D37CC"
    ),
}

KNOWN_REQUIRED_COLUMNS = {
    "shops": {"owner_name"},
    "customers": {"customer_name", "gst_number"},
    "stocks": {"k_minimum_stock", "r_minimum_stock"},
    "purchases": {"gst"},
    "purchase_items": {"total"},
    "purchase_return_items": {"total"},
    "supplier_payments": {"reference_number"},
    "tailoring_jobs": {"expected_date", "stitching_started_at"},
}

REJECTED_ALIASES = {
    "shops": {"owner"},
    "customers": {"name", "gst"},
    "stocks": {"k_min_stock", "r_min_stock", "quantity"},
    "purchases": {"gst_amount"},
    "purchase_items": {"total_price"},
    "purchase_return_items": {"total_price"},
    "supplier_payments": {"transaction_reference"},
    "tailoring_jobs": {"expected_delivery_date", "started_at"},
    "product_variants": {"stock"},
}


def _canonical_files() -> list[Path]:
    return sorted(
        path
        for path in CANONICAL_VERSIONS.glob("*.py")
        if path.name != "__init__.py"
    )


def _load_migration():
    files = _canonical_files()
    if len(files) != 1:
        raise AssertionError(f"Expected one canonical revision file, found {files}")
    spec = importlib.util.spec_from_file_location("canonical_baseline", files[0])
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load canonical revision: {files[0]}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return files[0], module


class CanonicalAlembicBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.migration_path, cls.migration = _load_migration()
        cls.source = cls.migration_path.read_text(encoding="utf-8")

    def _candidate_with_approved_differences(self):
        candidate = deepcopy(self.contract)
        candidate["provenance"]["database_name"] = "disposable_baseline_test"
        candidate["provenance"]["source_alembic_revision"] = "b1c27a4e6f0"
        for table in candidate["tables"]:
            table["indexes"] = [
                index
                for index in table["indexes"]
                if (table["name"], index["index_name"])
                not in ALLOWED_REDUNDANT_INDEXES
            ]
        return candidate

    @staticmethod
    def _table(contract, table_name):
        return next(table for table in contract["tables"] if table["name"] == table_name)

    def test_alembic_uses_only_canonical_version_location(self) -> None:
        config = Config(str(ALEMBIC_INI))
        scripts = ScriptDirectory.from_config(config)
        configured_locations = {
            Path(location).resolve() for location in scripts.version_locations
        }
        self.assertEqual({CANONICAL_VERSIONS.resolve()}, configured_locations)
        self.assertNotIn(HISTORICAL_VERSIONS.resolve(), configured_locations)

    def test_one_active_revision_is_root_and_head(self) -> None:
        config = Config(str(ALEMBIC_INI))
        scripts = ScriptDirectory.from_config(config)
        revisions = list(scripts.walk_revisions())

        self.assertEqual(1, len(_canonical_files()))
        self.assertEqual(1, len(revisions))
        self.assertIsNone(revisions[0].down_revision)
        self.assertEqual([revisions[0].revision], scripts.get_bases())
        self.assertEqual([revisions[0].revision], scripts.get_heads())
        self.assertEqual("b1c27a4e6f0", revisions[0].revision)

    def test_historical_migrations_match_commit_524f768(self) -> None:
        actual_files = {
            path.name for path in HISTORICAL_VERSIONS.glob("*.py")
        }
        self.assertEqual(set(HISTORICAL_MIGRATION_HASHES), actual_files)
        for filename, expected_hash in HISTORICAL_MIGRATION_HASHES.items():
            with self.subTest(filename=filename):
                content = (HISTORICAL_VERSIONS / filename).read_bytes()
                self.assertEqual(expected_hash, hashlib.sha256(content).hexdigest().upper())

    def test_migration_is_self_contained(self) -> None:
        tree = ast.parse(self.source, filename=str(self.migration_path))
        imported_modules = {
            alias.name
            for node in tree.body
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_from = {
            node.module for node in tree.body if isinstance(node, ast.ImportFrom)
        }
        called_attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }

        self.assertNotIn("json", imported_modules)
        self.assertNotIn("pathlib", imported_from)
        self.assertNotIn("read_text", called_attributes)
        self.assertNotIn("open", called_attributes)
        self.assertNotIn("schema_contract", self.source)

    def test_manifest_matches_contract_tables_columns_and_constraints(self) -> None:
        expected_tables = {table["name"]: table for table in self.contract["tables"]}
        actual_tables = {
            table["name"]: table for table in self.migration.BASELINE_MANIFEST["tables"]
        }
        self.assertEqual(set(expected_tables), set(actual_tables))
        self.assertEqual(27, len(actual_tables))
        self.assertEqual(
            298,
            sum(len(table["columns"]) for table in actual_tables.values()),
        )

        for table_name, expected in expected_tables.items():
            with self.subTest(table=table_name):
                actual = actual_tables[table_name]
                self.assertEqual(expected["columns"], actual["columns"])
                self.assertEqual(expected["primary_key"], actual["primary_key"])
                self.assertEqual(expected["foreign_keys"], actual["foreign_keys"])
                self.assertEqual(
                    expected["unique_constraints"], actual["unique_constraints"]
                )
                self.assertEqual(
                    expected["check_constraints"], actual["check_constraints"]
                )

    def test_foreign_key_actions_match_contract(self) -> None:
        expected = {
            (table["name"], foreign_key["constraint_name"]): (
                foreign_key["on_update"],
                foreign_key["on_delete"],
            )
            for table in self.contract["tables"]
            for foreign_key in table["foreign_keys"]
        }
        actual = {
            (table["name"], foreign_key["constraint_name"]): (
                foreign_key["on_update"],
                foreign_key["on_delete"],
            )
            for table in self.migration.BASELINE_MANIFEST["tables"]
            for foreign_key in table["foreign_keys"]
        }
        self.assertEqual(expected, actual)

    def test_indexes_match_except_allowlisted_redundant_indexes(self) -> None:
        expected_omitted = {
            index["index_name"]
            for table in self.contract["tables"]
            for index in table["indexes"]
            if index["redundant_primary_key_columns"]
        }
        self.assertEqual(
            {index_name for _, index_name in ALLOWED_REDUNDANT_INDEXES},
            expected_omitted,
        )
        self.assertEqual(
            expected_omitted, set(self.migration.OMITTED_LEGACY_REDUNDANT_INDEXES)
        )

        expected_indexes = {
            table["name"]: [
                index
                for index in table["indexes"]
                if not index["redundant_primary_key_columns"]
            ]
            for table in self.contract["tables"]
        }
        actual_indexes = {
            table["name"]: table["indexes"]
            for table in self.migration.BASELINE_MANIFEST["tables"]
        }
        self.assertEqual(expected_indexes, actual_indexes)
        self.assertEqual(66, sum(len(indexes) for indexes in actual_indexes.values()))

    def test_sequences_and_enum_match_contract(self) -> None:
        self.assertEqual(
            self.contract["sequences"], self.migration.BASELINE_MANIFEST["sequences"]
        )
        self.assertEqual(27, len(self.migration.BASELINE_MANIFEST["sequences"]))
        self.assertEqual(self.contract["enums"], self.migration.BASELINE_MANIFEST["enums"])
        self.assertEqual(
            ("SUPER_ADMIN", "ADMIN", "MANAGER", "CASHIER"),
            self.migration.USERROLE_VALUES,
        )
        self.assertFalse(self.migration.USERROLE_COLUMN_TYPE.create_type)

    def test_upgrade_records_complete_schema_without_database(self) -> None:
        with (
            mock.patch.object(self.migration.op, "get_bind", return_value=object()),
            mock.patch.object(self.migration.op, "execute") as execute,
            mock.patch.object(self.migration.op, "create_table") as create_table,
            mock.patch.object(self.migration.op, "create_index") as create_index,
            mock.patch.object(self.migration.USERROLE_DDL, "create") as create_enum,
        ):
            self.migration.upgrade()

        create_enum.assert_called_once_with(mock.ANY, checkfirst=False)
        self.assertEqual(27, create_table.call_count)
        self.assertEqual(
            set(self.migration.TABLE_CREATION_ORDER),
            {call.args[0] for call in create_table.call_args_list},
        )
        self.assertEqual(25, create_index.call_count)
        self.assertEqual(54, execute.call_count)
        self.assertEqual(
            27,
            sum(
                isinstance(call.args[0], sa.schema.CreateSequence)
                for call in execute.call_args_list
            ),
        )

    def test_table_creation_order_satisfies_foreign_keys(self) -> None:
        positions = {
            table_name: position
            for position, table_name in enumerate(self.migration.TABLE_CREATION_ORDER)
        }
        self.assertEqual(
            {table["name"] for table in self.contract["tables"]}, set(positions)
        )
        for table in self.contract["tables"]:
            for foreign_key in table["foreign_keys"]:
                referenced = foreign_key["referenced_table"]
                if referenced == table["name"]:
                    continue
                self.assertLess(
                    positions[referenced],
                    positions[table["name"]],
                    msg=f"{table['name']} precedes dependency {referenced}",
                )

    def test_no_business_data_or_sequence_state_operations(self) -> None:
        forbidden = re.compile(
            r"\b(?:INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|TRUNCATE|"
            r"setval\s*\(|RESTART\s+WITH|last_value|is_called)\b",
            flags=re.IGNORECASE,
        )
        self.assertIsNone(forbidden.search(self.source))

    def test_downgrade_raises_before_any_alembic_operation(self) -> None:
        tree = ast.parse(self.source, filename=str(self.migration_path))
        downgrade = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "downgrade"
        )
        self.assertEqual(1, len(downgrade.body))
        self.assertIsInstance(downgrade.body[0], ast.Raise)
        with self.assertRaisesRegex(RuntimeError, "intentionally unsupported"):
            self.migration.downgrade()

    def test_known_names_preserved_and_rejected_aliases_absent(self) -> None:
        tables = {
            table["name"]: {
                column["column_name"] for column in table["columns"]
            }
            for table in self.migration.BASELINE_MANIFEST["tables"]
        }
        for table_name, required in KNOWN_REQUIRED_COLUMNS.items():
            self.assertTrue(required <= tables[table_name])
        for table_name, forbidden in REJECTED_ALIASES.items():
            self.assertTrue(forbidden.isdisjoint(tables[table_name]))

    def test_documentation_records_rebaseline_safety(self) -> None:
        readme = (CANONICAL_VERSIONS / "README.md").read_text(encoding="utf-8")
        normalized_readme = " ".join(readme.split())
        for required_text in (
            "ce97b6c5d53e",
            "524f768",
            "intentionally excluded",
            "separately reviewed manual stamp",
            "Never run this root migration against `bhavani_erp_v2`",
            "No live stamp is part of this change",
        ):
            self.assertIn(required_text, normalized_readme)

    def test_comparison_ignores_only_approved_differences(self) -> None:
        candidate = self._candidate_with_approved_differences()
        self.assertEqual([], compare_contracts(self.contract, candidate))

        changed = deepcopy(candidate)
        changed["tables"][0]["columns"][0]["nullable"] = not changed["tables"][0][
            "columns"
        ][0]["nullable"]
        self.assertTrue(compare_contracts(self.contract, changed))

        changed = deepcopy(candidate)
        changed["tables"][0]["unexpected_field"] = "must not be ignored"
        self.assertTrue(compare_contracts(self.contract, changed))

    def test_comparison_normalizes_sparse_column_ordinals(self) -> None:
        authoritative = deepcopy(self.contract)
        candidate = self._candidate_with_approved_differences()
        authoritative_columns = authoritative["tables"][0]["columns"]
        candidate_columns = candidate["tables"][0]["columns"]
        for position, column in enumerate(authoritative_columns, start=1):
            column["ordinal_position"] = position * 3
        for position, column in enumerate(candidate_columns, start=1):
            column["ordinal_position"] = position
        self.assertEqual([], compare_contracts(authoritative, candidate))

    def test_comparison_rejects_reordered_columns(self) -> None:
        candidate = self._candidate_with_approved_differences()
        columns = candidate["tables"][0]["columns"]
        columns[0], columns[1] = columns[1], columns[0]
        for position, column in enumerate(columns, start=1):
            column["ordinal_position"] = position
        self.assertTrue(compare_contracts(self.contract, candidate))

    def test_comparison_rejects_missing_and_extra_columns(self) -> None:
        missing = self._candidate_with_approved_differences()
        missing["tables"][0]["columns"].pop()
        self.assertTrue(compare_contracts(self.contract, missing))

        extra = self._candidate_with_approved_differences()
        columns = extra["tables"][0]["columns"]
        added = deepcopy(columns[-1])
        added["column_name"] = "unexpected_extra_column"
        added["ordinal_position"] = columns[-1]["ordinal_position"] + 1
        columns.append(added)
        self.assertTrue(compare_contracts(self.contract, extra))

    def test_comparison_preserves_all_nonordinal_column_semantics(self) -> None:
        mutations = {
            "data_type": "bigint",
            "formatted_type": "bigint",
            "nullable": True,
            "server_default": None,
            "identity_generation": "ALWAYS",
            "generated_kind": "s",
            "generation_expression": "1",
        }
        for field, replacement in mutations.items():
            with self.subTest(field=field):
                candidate = self._candidate_with_approved_differences()
                column = candidate["tables"][0]["columns"][0]
                self.assertNotEqual(replacement, column[field])
                column[field] = replacement
                self.assertTrue(compare_contracts(self.contract, candidate))

    def test_comparison_rejects_duplicate_and_non_increasing_ordinals(self) -> None:
        duplicate = self._candidate_with_approved_differences()
        columns = duplicate["tables"][0]["columns"]
        columns[1]["ordinal_position"] = columns[0]["ordinal_position"]
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            compare_contracts(self.contract, duplicate)

        decreasing = self._candidate_with_approved_differences()
        columns = decreasing["tables"][0]["columns"]
        columns[1]["ordinal_position"] = columns[0]["ordinal_position"] - 1
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            compare_contracts(self.contract, decreasing)

    def test_comparison_accepts_only_observed_tailoring_check_renderings(self) -> None:
        authoritative = deepcopy(self.contract)
        candidate = self._candidate_with_approved_differences()
        expressions = sorted(TAILORING_STOCK_TYPE_CHECK_EXPRESSIONS)

        for contract, expression in zip((authoritative, candidate), expressions):
            table = self._table(contract, "tailoring_jobs")
            constraint = next(
                check
                for check in table["check_constraints"]
                if check["constraint_name"] == "tailoring_jobs_stock_type_check"
            )
            constraint["expression"] = expression

        self.assertEqual([], compare_contracts(authoritative, candidate))

        changed = deepcopy(candidate)
        table = self._table(changed, "tailoring_jobs")
        constraint = next(
            check
            for check in table["check_constraints"]
            if check["constraint_name"] == "tailoring_jobs_stock_type_check"
        )
        constraint["expression"] = constraint["expression"].replace("'R'", "'X'")
        self.assertTrue(compare_contracts(authoritative, changed))

    def test_comparison_rejects_other_check_constraint_difference(self) -> None:
        candidate = self._candidate_with_approved_differences()
        table = self._table(candidate, "tailoring_jobs")
        constraint = next(
            check
            for check in table["check_constraints"]
            if check["constraint_name"] != "tailoring_jobs_stock_type_check"
        )
        constraint["expression"] = f"({constraint['expression']}) AND true"
        self.assertTrue(compare_contracts(self.contract, candidate))

    def test_comparison_rejects_unexpected_redundant_index(self) -> None:
        candidate = deepcopy(self.contract)
        index = candidate["tables"][0]["indexes"][0]
        index["redundant_primary_key_columns"] = True
        identity = (candidate["tables"][0]["name"], index["index_name"])
        if identity in ALLOWED_REDUNDANT_INDEXES:
            self.skipTest("Fixture unexpectedly selected an allowlisted index")
        with self.assertRaisesRegex(ValueError, "Unexpected redundant index"):
            compare_contracts(self.contract, candidate)


if __name__ == "__main__":
    unittest.main()
