import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest import mock

from scripts import export_postgres_schema_contract as exporter


normalize_sql_expression = exporter.normalize_sql_expression
render_contract = exporter.render_contract


BACKEND_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    BACKEND_ROOT / "schema_contract" / "bhavani_erp_v2_live_schema.json"
)

EXPECTED_TABLES = {
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
}


def _mock_snapshot_sections(
    database_name: str = "bhavani_erp_v2",
    transaction_read_only: str = "on",
) -> dict[str, list[dict]]:
    table_names = sorted(EXPECTED_TABLES)
    return {
        "provenance": [
            {
                "database_name": database_name,
                "transaction_read_only": transaction_read_only,
                "postgresql_server_version": "18.4",
                "alembic_revision": "ce97b6c5d53e",
            }
        ],
        "tables": [{"table_name": table_name} for table_name in table_names],
        "columns": [
            {
                "table_name": table_name,
                "ordinal_position": 1,
                "column_name": "id",
                "data_type": "integer",
                "formatted_type": "integer",
                "nullable": False,
                "server_default": None,
                "identity_generation": None,
                "generated_kind": None,
                "generation_expression": None,
            }
            for table_name in table_names
        ],
        "primary_keys": [
            {
                "table_name": table_name,
                "constraint_name": f"{table_name}_pkey",
                "columns": ["id"],
            }
            for table_name in table_names
        ],
        "foreign_keys": [],
        "unique_constraints": [],
        "check_constraints": [],
        "indexes": [
            {
                "table_name": table_name,
                "index_name": f"{table_name}_pkey",
                "unique": True,
                "primary": True,
                "method": "btree",
                "key_expressions": ["id"],
                "included_columns": [],
                "predicate": None,
                "valid": True,
                "ready": True,
                "constraint_name": f"{table_name}_pkey",
                "constraint_type": "p",
            }
            for table_name in table_names
        ],
        "sequences": [
            {
                "sequence_name": f"{table_name}_id_seq",
                "data_type": "integer",
                "start_value": 1,
                "increment_by": 1,
                "minimum_value": 1,
                "maximum_value": 2147483647,
                "cache_size": 1,
                "cycle": False,
                "owned_by_schema": "public",
                "owned_by_table": table_name,
                "owned_by_column": "id",
            }
            for table_name in table_names
        ],
        "enums": [
            {
                "enum_name": "userrole",
                "values": ["SUPER_ADMIN", "ADMIN", "MANAGER", "CASHIER"],
            }
        ],
        "catalog_counts": [
            {
                "application_tables": 27,
                "columns": 27,
                "primary_keys": 27,
                "tables_with_exactly_one_primary_key": 27,
                "foreign_keys": 0,
                "unique_constraints": 0,
                "check_constraints": 0,
                "sequences": 27,
                "enums": 1,
                "total_physical_indexes": 27,
                "primary_key_backed_indexes": 27,
                "unique_constraint_backed_indexes": 0,
                "other_unique_indexes": 0,
                "nonunique_secondary_indexes": 0,
                "redundant_primary_key_column_indexes": 0,
            }
        ],
    }


def _encode_mock_snapshot(sections: dict[str, list[dict]]) -> str:
    return "\n".join(
        f"{exporter.SECTION_PREFIX}{label}:"
        f"{json.dumps(sections[label], separators=(',', ':'))}"
        for label, _, _ in exporter.SNAPSHOT_QUERIES
    ) + "\n"


def _successful_psql_result(
    sections: dict[str, list[dict]] | None = None,
) -> subprocess.CompletedProcess:
    if sections is None:
        sections = _mock_snapshot_sections()
    return subprocess.CompletedProcess(
        args=["psql"],
        returncode=0,
        stdout=_encode_mock_snapshot(sections),
        stderr="",
    )


class SchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = CONTRACT_PATH.read_text(encoding="utf-8")
        cls.contract = json.loads(cls.source)
        cls.tables = {table["name"]: table for table in cls.contract["tables"]}

    def column_names(self, table_name: str) -> set[str]:
        return {
            column["column_name"] for column in self.tables[table_name]["columns"]
        }

    def test_contract_is_canonical_json(self) -> None:
        self.assertEqual(render_contract(self.contract), self.source)

    def test_exact_application_table_manifest(self) -> None:
        self.assertEqual(27, self.contract["application_table_count"])
        self.assertEqual(EXPECTED_TABLES, set(self.tables))
        self.assertNotIn("alembic_version", self.tables)
        self.assertEqual(sorted(self.tables), [table["name"] for table in self.contract["tables"]])

    def test_provenance_is_complete_and_stable(self) -> None:
        self.assertEqual(1, self.contract["format_version"])
        self.assertEqual(
            {
                "database_name",
                "postgresql_server_version",
                "source_alembic_revision",
            },
            set(self.contract["provenance"]),
        )
        self.assertEqual(
            "ce97b6c5d53e",
            self.contract["provenance"]["source_alembic_revision"],
        )
        self.assertTrue(self.contract["provenance"]["postgresql_server_version"])

    def test_verified_live_column_names(self) -> None:
        required = {
            "shops": {"owner_name"},
            "customers": {"customer_name", "gst_number"},
            "stocks": {"k_minimum_stock", "r_minimum_stock"},
            "purchases": {"gst"},
            "purchase_items": {"total"},
            "purchase_return_items": {"total"},
            "supplier_payments": {"reference_number"},
            "tailoring_jobs": {"expected_date", "stitching_started_at"},
        }
        forbidden = {
            "shops": {"owner"},
            "customers": {"name", "gst"},
            "stocks": {"k_min_stock", "r_min_stock"},
            "purchases": {"gst_amount"},
            "purchase_items": {"total_price"},
            "purchase_return_items": {"total_price"},
            "supplier_payments": {"transaction_reference"},
            "tailoring_jobs": {"expected_delivery_date", "started_at"},
        }

        for table_name, names in required.items():
            with self.subTest(table=table_name, kind="required"):
                self.assertTrue(names <= self.column_names(table_name))
        for table_name, names in forbidden.items():
            with self.subTest(table=table_name, kind="forbidden"):
                self.assertTrue(names.isdisjoint(self.column_names(table_name)))

    def test_every_table_has_columns_and_one_primary_key(self) -> None:
        for table in self.contract["tables"]:
            with self.subTest(table=table["name"]):
                self.assertTrue(table["columns"])
                self.assertTrue(table["primary_key"]["constraint_name"])
                self.assertTrue(table["primary_key"]["columns"])

    def test_independent_catalog_counts_reconcile(self) -> None:
        counts = self.contract["catalog_counts"]
        self.assertEqual(27, counts["application_tables"])
        self.assertEqual(299 - 1, counts["columns"])
        self.assertEqual(27, counts["primary_keys"])
        self.assertEqual(27, counts["tables_with_exactly_one_primary_key"])
        self.assertEqual(54, counts["foreign_keys"])
        self.assertEqual(14, counts["unique_constraints"])
        self.assertEqual(8, counts["check_constraints"])
        self.assertEqual(27, counts["sequences"])
        self.assertEqual(1, counts["enums"])

        index_counts = counts["indexes"]
        self.assertEqual(
            {
                "total_physical": 76,
                "primary_key_backed": 27,
                "unique_constraint_backed": 14,
                "other_unique": 1,
                "nonunique_secondary": 34,
                "redundant_primary_key_columns": 10,
            },
            index_counts,
        )
        exported_index_count = sum(
            len(table["indexes"]) for table in self.contract["tables"]
        )
        self.assertEqual(index_counts["total_physical"], exported_index_count)
        self.assertEqual(
            index_counts["total_physical"],
            sum(
                index_counts[category]
                for category in (
                    "primary_key_backed",
                    "unique_constraint_backed",
                    "other_unique",
                    "nonunique_secondary",
                )
            ),
        )

    def test_foreign_keys_reference_contract_tables(self) -> None:
        for table in self.contract["tables"]:
            for foreign_key in table["foreign_keys"]:
                with self.subTest(
                    table=table["name"], foreign_key=foreign_key["constraint_name"]
                ):
                    self.assertEqual("public", foreign_key["referenced_schema"])
                    self.assertIn(foreign_key["referenced_table"], self.tables)

    def test_collection_order_is_deterministic(self) -> None:
        self.assertEqual(
            sorted(sequence["sequence_name"] for sequence in self.contract["sequences"]),
            [sequence["sequence_name"] for sequence in self.contract["sequences"]],
        )
        self.assertEqual(
            sorted(enum["enum_name"] for enum in self.contract["enums"]),
            [enum["enum_name"] for enum in self.contract["enums"]],
        )
        for table in self.contract["tables"]:
            with self.subTest(table=table["name"]):
                self.assertEqual(
                    sorted(
                        table["columns"], key=lambda column: column["ordinal_position"]
                    ),
                    table["columns"],
                )
                for key, name_key in (
                    ("foreign_keys", "constraint_name"),
                    ("unique_constraints", "constraint_name"),
                    ("check_constraints", "constraint_name"),
                    ("indexes", "index_name"),
                ):
                    self.assertEqual(
                        sorted(table[key], key=lambda item: item[name_key]), table[key]
                    )

    def test_sequences_contain_definition_without_runtime_state(self) -> None:
        self.assertTrue(self.contract["sequences"])
        self.assertEqual(
            len(self.contract["sequences"]),
            len(
                {
                    sequence["sequence_name"]
                    for sequence in self.contract["sequences"]
                }
            ),
        )
        required = {
            "sequence_name",
            "data_type",
            "start_value",
            "increment_by",
            "minimum_value",
            "maximum_value",
            "cache_size",
            "cycle",
            "owned_by_schema",
            "owned_by_table",
            "owned_by_column",
        }
        for sequence in self.contract["sequences"]:
            self.assertEqual(required, set(sequence))
            self.assertNotIn("last_value", sequence)
            self.assertNotIn("is_called", sequence)

    def test_contract_has_no_connection_or_credential_values(self) -> None:
        self.assertNotIn("DATABASE_URL", self.source)
        self.assertNotRegex(self.source, re.compile(r"postgres(?:ql)?://", re.I))
        self.assertNotIn("connection_string", self.source.lower())
        self.assertNotIn("database_url", self.source.lower())
        self.assertEqual("bhavani_erp_v2", self.contract["provenance"]["database_name"])

    def test_userrole_enum_is_recorded(self) -> None:
        enums = {item["enum_name"]: item["values"] for item in self.contract["enums"]}
        self.assertEqual(
            ["SUPER_ADMIN", "ADMIN", "MANAGER", "CASHIER"], enums["userrole"]
        )

    def test_normalization_collapses_only_unquoted_whitespace(self) -> None:
        self.assertEqual(
            "amount >= 0 AND method = 'Cash  Sale'",
            normalize_sql_expression(
                "  amount  >=\n0  AND method = 'Cash  Sale'  "
            ),
        )
        self.assertEqual(
            'lower( "Odd  Name" )',
            normalize_sql_expression(' lower(  "Odd  Name" ) '),
        )
        self.assertIsNone(normalize_sql_expression(None))

    def test_complete_export_uses_one_psql_subprocess_and_one_snapshot(self) -> None:
        with (
            mock.patch.object(exporter, "_find_psql", return_value="psql"),
            mock.patch.object(exporter, "_psql_environment", return_value={}),
            mock.patch.object(
                exporter.subprocess,
                "run",
                return_value=_successful_psql_result(),
            ) as run,
        ):
            contract = exporter.export_contract()

        self.assertEqual(27, contract["application_table_count"])
        run.assert_called_once()
        script = run.call_args.kwargs["input"]
        self.assertEqual(
            1,
            script.count(
                "BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;"
            ),
        )
        for label, _, _ in exporter.SNAPSHOT_QUERIES:
            self.assertIn(f"{exporter.SECTION_PREFIX}{label}:", script)

    def test_failed_psql_does_not_replace_existing_output(self) -> None:
        failed_result = subprocess.CompletedProcess(
            args=["psql"], returncode=3, stdout="", stderr="catalog query failed"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "contract.json"
            output_path.write_text("existing contract\n", encoding="utf-8")
            with (
                mock.patch.object(exporter, "_find_psql", return_value="psql"),
                mock.patch.object(exporter, "_psql_environment", return_value={}),
                mock.patch.object(
                    exporter.subprocess, "run", return_value=failed_result
                ) as run,
                self.assertRaisesRegex(RuntimeError, "snapshot failed"),
            ):
                exporter.export_to_path(output_path)

            run.assert_called_once()
            self.assertEqual(
                "existing contract\n", output_path.read_text(encoding="utf-8")
            )

    def test_unexpected_database_or_non_read_only_snapshot_fails(self) -> None:
        invalid_provenance = (
            ("wrong_database", "on", "database verification failed"),
            ("bhavani_erp_v2", "off", "transaction was not read only"),
        )
        for database_name, read_only, message in invalid_provenance:
            with self.subTest(database=database_name, read_only=read_only):
                sections = _mock_snapshot_sections(database_name, read_only)
                with (
                    mock.patch.object(exporter, "_find_psql", return_value="psql"),
                    mock.patch.object(
                        exporter, "_psql_environment", return_value={}
                    ),
                    mock.patch.object(
                        exporter.subprocess,
                        "run",
                        return_value=_successful_psql_result(sections),
                    ) as run,
                    self.assertRaisesRegex(RuntimeError, message),
                ):
                    exporter.export_contract()
                run.assert_called_once()

    def test_canonical_rendering_is_deterministic_for_fixture(self) -> None:
        first = {"z": [3, 2, 1], "a": {"second": 2, "first": 1}}
        second = {"a": {"first": 1, "second": 2}, "z": [3, 2, 1]}
        self.assertEqual(render_contract(first), render_contract(second))


if __name__ == "__main__":
    unittest.main()
