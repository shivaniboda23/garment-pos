"""Export the authoritative PostgreSQL storage schema as canonical JSON.

The exporter uses PostgreSQL's catalog through exactly one ``psql`` subprocess
and one repeatable-read, read-only transaction. It refuses to run unless
connected to the expected application database.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import glob
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit


EXPECTED_DATABASE = "bhavani_erp_v2"
FORMAT_VERSION = 1
BACKEND_ROOT = Path(__file__).resolve().parents[1]
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


TABLES_SQL = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
  AND table_name <> 'alembic_version'
"""

COLUMNS_SQL = """
SELECT
    cls.relname AS table_name,
    attr.attnum AS ordinal_position,
    attr.attname AS column_name,
    cols.data_type,
    pg_catalog.format_type(attr.atttypid, attr.atttypmod) AS formatted_type,
    NOT attr.attnotnull AS nullable,
    pg_catalog.pg_get_expr(def.adbin, def.adrelid, true) AS server_default,
    CASE attr.attidentity
        WHEN 'a' THEN 'ALWAYS'
        WHEN 'd' THEN 'BY DEFAULT'
        ELSE NULL
    END AS identity_generation,
    CASE attr.attgenerated
        WHEN 's' THEN 'STORED'
        WHEN 'v' THEN 'VIRTUAL'
        ELSE NULL
    END AS generated_kind,
    CASE
        WHEN attr.attgenerated <> ''
        THEN pg_catalog.pg_get_expr(def.adbin, def.adrelid, true)
        ELSE NULL
    END AS generation_expression
FROM pg_catalog.pg_class AS cls
JOIN pg_catalog.pg_namespace AS ns ON ns.oid = cls.relnamespace
JOIN pg_catalog.pg_attribute AS attr ON attr.attrelid = cls.oid
JOIN information_schema.columns AS cols
  ON cols.table_schema = ns.nspname
 AND cols.table_name = cls.relname
 AND cols.column_name = attr.attname
LEFT JOIN pg_catalog.pg_attrdef AS def
  ON def.adrelid = attr.attrelid
 AND def.adnum = attr.attnum
WHERE ns.nspname = 'public'
  AND cls.relkind IN ('r', 'p')
  AND cls.relname <> 'alembic_version'
  AND attr.attnum > 0
  AND NOT attr.attisdropped
"""

PRIMARY_KEYS_SQL = """
SELECT
    rel.relname AS table_name,
    con.conname AS constraint_name,
    ARRAY(
        SELECT attr.attname
        FROM unnest(con.conkey) WITH ORDINALITY AS key(attnum, position)
        JOIN pg_catalog.pg_attribute AS attr
          ON attr.attrelid = con.conrelid
         AND attr.attnum = key.attnum
        ORDER BY key.position
    ) AS columns
FROM pg_catalog.pg_constraint AS con
JOIN pg_catalog.pg_class AS rel ON rel.oid = con.conrelid
JOIN pg_catalog.pg_namespace AS ns ON ns.oid = rel.relnamespace
WHERE ns.nspname = 'public'
  AND rel.relname <> 'alembic_version'
  AND con.contype = 'p'
"""

FOREIGN_KEYS_SQL = """
SELECT
    rel.relname AS table_name,
    con.conname AS constraint_name,
    ARRAY(
        SELECT attr.attname
        FROM unnest(con.conkey) WITH ORDINALITY AS key(attnum, position)
        JOIN pg_catalog.pg_attribute AS attr
          ON attr.attrelid = con.conrelid
         AND attr.attnum = key.attnum
        ORDER BY key.position
    ) AS columns,
    ref_ns.nspname AS referenced_schema,
    ref_rel.relname AS referenced_table,
    ARRAY(
        SELECT attr.attname
        FROM unnest(con.confkey) WITH ORDINALITY AS key(attnum, position)
        JOIN pg_catalog.pg_attribute AS attr
          ON attr.attrelid = con.confrelid
         AND attr.attnum = key.attnum
        ORDER BY key.position
    ) AS referenced_columns,
    CASE con.confupdtype
        WHEN 'a' THEN 'NO ACTION'
        WHEN 'r' THEN 'RESTRICT'
        WHEN 'c' THEN 'CASCADE'
        WHEN 'n' THEN 'SET NULL'
        WHEN 'd' THEN 'SET DEFAULT'
    END AS on_update,
    CASE con.confdeltype
        WHEN 'a' THEN 'NO ACTION'
        WHEN 'r' THEN 'RESTRICT'
        WHEN 'c' THEN 'CASCADE'
        WHEN 'n' THEN 'SET NULL'
        WHEN 'd' THEN 'SET DEFAULT'
    END AS on_delete,
    con.condeferrable AS deferrable,
    con.condeferred AS initially_deferred,
    con.convalidated AS validated
FROM pg_catalog.pg_constraint AS con
JOIN pg_catalog.pg_class AS rel ON rel.oid = con.conrelid
JOIN pg_catalog.pg_namespace AS ns ON ns.oid = rel.relnamespace
JOIN pg_catalog.pg_class AS ref_rel ON ref_rel.oid = con.confrelid
JOIN pg_catalog.pg_namespace AS ref_ns ON ref_ns.oid = ref_rel.relnamespace
WHERE ns.nspname = 'public'
  AND rel.relname <> 'alembic_version'
  AND con.contype = 'f'
"""

UNIQUE_CONSTRAINTS_SQL = """
SELECT
    rel.relname AS table_name,
    con.conname AS constraint_name,
    ARRAY(
        SELECT attr.attname
        FROM unnest(con.conkey) WITH ORDINALITY AS key(attnum, position)
        JOIN pg_catalog.pg_attribute AS attr
          ON attr.attrelid = con.conrelid
         AND attr.attnum = key.attnum
        ORDER BY key.position
    ) AS columns,
    con.condeferrable AS deferrable,
    con.condeferred AS initially_deferred,
    con.convalidated AS validated
FROM pg_catalog.pg_constraint AS con
JOIN pg_catalog.pg_class AS rel ON rel.oid = con.conrelid
JOIN pg_catalog.pg_namespace AS ns ON ns.oid = rel.relnamespace
WHERE ns.nspname = 'public'
  AND rel.relname <> 'alembic_version'
  AND con.contype = 'u'
"""

CHECK_CONSTRAINTS_SQL = """
SELECT
    rel.relname AS table_name,
    con.conname AS constraint_name,
    pg_catalog.pg_get_expr(con.conbin, con.conrelid, true) AS expression,
    con.convalidated AS validated,
    con.connoinherit AS no_inherit
FROM pg_catalog.pg_constraint AS con
JOIN pg_catalog.pg_class AS rel ON rel.oid = con.conrelid
JOIN pg_catalog.pg_namespace AS ns ON ns.oid = rel.relnamespace
WHERE ns.nspname = 'public'
  AND rel.relname <> 'alembic_version'
  AND con.contype = 'c'
"""

INDEXES_SQL = """
SELECT
    rel.relname AS table_name,
    idx_rel.relname AS index_name,
    idx.indisunique AS unique,
    idx.indisprimary AS primary,
    method.amname AS method,
    ARRAY(
        SELECT pg_catalog.pg_get_indexdef(idx.indexrelid, position, true)
        FROM generate_series(1, idx.indnkeyatts) AS position
        ORDER BY position
    ) AS key_expressions,
    ARRAY(
        SELECT pg_catalog.pg_get_indexdef(idx.indexrelid, position, true)
        FROM generate_series(idx.indnkeyatts + 1, idx.indnatts) AS position
        ORDER BY position
    ) AS included_columns,
    pg_catalog.pg_get_expr(idx.indpred, idx.indrelid, true) AS predicate,
    idx.indisvalid AS valid,
    idx.indisready AS ready,
    (
        SELECT con.conname
        FROM pg_catalog.pg_constraint AS con
        WHERE con.conindid = idx.indexrelid
          AND con.contype IN ('p', 'u', 'x')
    ) AS constraint_name,
    (
        SELECT con.contype::text
        FROM pg_catalog.pg_constraint AS con
        WHERE con.conindid = idx.indexrelid
          AND con.contype IN ('p', 'u', 'x')
    ) AS constraint_type
FROM pg_catalog.pg_index AS idx
JOIN pg_catalog.pg_class AS rel ON rel.oid = idx.indrelid
JOIN pg_catalog.pg_namespace AS ns ON ns.oid = rel.relnamespace
JOIN pg_catalog.pg_class AS idx_rel ON idx_rel.oid = idx.indexrelid
JOIN pg_catalog.pg_am AS method ON method.oid = idx_rel.relam
WHERE ns.nspname = 'public'
  AND rel.relname <> 'alembic_version'
"""

SEQUENCES_SQL = """
SELECT
    seq_rel.relname AS sequence_name,
    pg_catalog.format_type(seq.seqtypid, NULL) AS data_type,
    seq.seqstart AS start_value,
    seq.seqincrement AS increment_by,
    seq.seqmin AS minimum_value,
    seq.seqmax AS maximum_value,
    seq.seqcache AS cache_size,
    seq.seqcycle AS cycle,
    owner.owned_by_schema,
    owner.owned_by_table,
    owner.owned_by_column
FROM pg_catalog.pg_sequence AS seq
JOIN pg_catalog.pg_class AS seq_rel ON seq_rel.oid = seq.seqrelid
JOIN pg_catalog.pg_namespace AS seq_ns ON seq_ns.oid = seq_rel.relnamespace
LEFT JOIN LATERAL (
    SELECT
        owner_ns.nspname AS owned_by_schema,
        owner_rel.relname AS owned_by_table,
        owner_attr.attname AS owned_by_column
    FROM pg_catalog.pg_depend AS dep
    JOIN pg_catalog.pg_class AS owner_rel ON owner_rel.oid = dep.refobjid
    JOIN pg_catalog.pg_namespace AS owner_ns ON owner_ns.oid = owner_rel.relnamespace
    JOIN pg_catalog.pg_attribute AS owner_attr
      ON owner_attr.attrelid = dep.refobjid
     AND owner_attr.attnum = dep.refobjsubid
    WHERE dep.classid = 'pg_class'::regclass
      AND dep.objid = seq_rel.oid
      AND dep.refclassid = 'pg_class'::regclass
      AND dep.deptype IN ('a', 'i')
    ORDER BY dep.refobjid, dep.refobjsubid
    LIMIT 1
) AS owner ON true
WHERE seq_ns.nspname = 'public'
"""

ENUMS_SQL = """
SELECT
    typ.typname AS enum_name,
    ARRAY(
        SELECT enum.enumlabel
        FROM pg_catalog.pg_enum AS enum
        WHERE enum.enumtypid = typ.oid
        ORDER BY enum.enumsortorder
    ) AS values
FROM pg_catalog.pg_type AS typ
JOIN pg_catalog.pg_namespace AS ns ON ns.oid = typ.typnamespace
WHERE ns.nspname = 'public'
  AND typ.typtype = 'e'
"""

PROVENANCE_SQL = """
SELECT
    current_database() AS database_name,
    current_setting('transaction_read_only') AS transaction_read_only,
    current_setting('server_version') AS postgresql_server_version,
    (SELECT version_num FROM public.alembic_version) AS alembic_revision
"""

CATALOG_COUNTS_SQL = """
WITH application_tables AS (
    SELECT cls.oid, cls.relname
    FROM pg_catalog.pg_class AS cls
    JOIN pg_catalog.pg_namespace AS ns ON ns.oid = cls.relnamespace
    WHERE ns.nspname = 'public'
      AND cls.relkind IN ('r', 'p')
      AND cls.relname <> 'alembic_version'
),
physical_indexes AS (
    SELECT
        idx.indexrelid,
        idx.indrelid,
        idx.indisprimary,
        idx.indisunique,
        idx.indpred,
        idx.indkey,
        idx.indnkeyatts,
        idx.indnatts,
        primary_key.conkey AS primary_key_columns,
        EXISTS (
            SELECT 1
            FROM pg_catalog.pg_constraint AS unique_constraint
            WHERE unique_constraint.conindid = idx.indexrelid
              AND unique_constraint.contype = 'u'
        ) AS unique_constraint_backed
    FROM pg_catalog.pg_index AS idx
    JOIN application_tables AS rel ON rel.oid = idx.indrelid
    LEFT JOIN pg_catalog.pg_constraint AS primary_key
      ON primary_key.conrelid = idx.indrelid
     AND primary_key.contype = 'p'
),
index_counts AS (
    SELECT
        COUNT(DISTINCT indexrelid) AS total_physical_indexes,
        COUNT(DISTINCT indexrelid) FILTER (
            WHERE indisprimary
        ) AS primary_key_backed_indexes,
        COUNT(DISTINCT indexrelid) FILTER (
            WHERE NOT indisprimary AND unique_constraint_backed
        ) AS unique_constraint_backed_indexes,
        COUNT(DISTINCT indexrelid) FILTER (
            WHERE indisunique
              AND NOT indisprimary
              AND NOT unique_constraint_backed
        ) AS other_unique_indexes,
        COUNT(DISTINCT indexrelid) FILTER (
            WHERE NOT indisunique
        ) AS nonunique_secondary_indexes,
        COUNT(DISTINCT indexrelid) FILTER (
            WHERE NOT indisprimary
              AND indpred IS NULL
              AND indnatts = indnkeyatts
              AND indnkeyatts = cardinality(primary_key_columns)
              AND ARRAY(
                  SELECT indkey[position - 1]
                  FROM generate_series(1, indnkeyatts) AS position
                  ORDER BY position
              ) = primary_key_columns
        ) AS redundant_primary_key_column_indexes
    FROM physical_indexes
)
SELECT
    (SELECT COUNT(*) FROM application_tables) AS application_tables,
    (
        SELECT COUNT(*)
        FROM pg_catalog.pg_attribute AS attr
        JOIN application_tables AS rel ON rel.oid = attr.attrelid
        WHERE attr.attnum > 0
          AND NOT attr.attisdropped
    ) AS columns,
    (
        SELECT COUNT(*)
        FROM pg_catalog.pg_constraint AS con
        JOIN application_tables AS rel ON rel.oid = con.conrelid
        WHERE con.contype = 'p'
    ) AS primary_keys,
    (
        SELECT COUNT(*)
        FROM (
            SELECT con.conrelid
            FROM pg_catalog.pg_constraint AS con
            JOIN application_tables AS rel ON rel.oid = con.conrelid
            WHERE con.contype = 'p'
            GROUP BY con.conrelid
            HAVING COUNT(*) = 1
        ) AS tables_with_one_primary_key
    ) AS tables_with_exactly_one_primary_key,
    (
        SELECT COUNT(*)
        FROM pg_catalog.pg_constraint AS con
        JOIN application_tables AS rel ON rel.oid = con.conrelid
        WHERE con.contype = 'f'
    ) AS foreign_keys,
    (
        SELECT COUNT(*)
        FROM pg_catalog.pg_constraint AS con
        JOIN application_tables AS rel ON rel.oid = con.conrelid
        WHERE con.contype = 'u'
    ) AS unique_constraints,
    (
        SELECT COUNT(*)
        FROM pg_catalog.pg_constraint AS con
        JOIN application_tables AS rel ON rel.oid = con.conrelid
        WHERE con.contype = 'c'
    ) AS check_constraints,
    (
        SELECT COUNT(DISTINCT seq.seqrelid)
        FROM pg_catalog.pg_sequence AS seq
        JOIN pg_catalog.pg_class AS seq_rel ON seq_rel.oid = seq.seqrelid
        JOIN pg_catalog.pg_namespace AS seq_ns ON seq_ns.oid = seq_rel.relnamespace
        WHERE seq_ns.nspname = 'public'
    ) AS sequences,
    (
        SELECT COUNT(*)
        FROM pg_catalog.pg_type AS typ
        JOIN pg_catalog.pg_namespace AS ns ON ns.oid = typ.typnamespace
        WHERE ns.nspname = 'public'
          AND typ.typtype = 'e'
    ) AS enums,
    index_counts.total_physical_indexes,
    index_counts.primary_key_backed_indexes,
    index_counts.unique_constraint_backed_indexes,
    index_counts.other_unique_indexes,
    index_counts.nonunique_secondary_indexes,
    index_counts.redundant_primary_key_column_indexes
FROM index_counts
"""


def normalize_sql_expression(value: str | None) -> str | None:
    """Collapse insignificant whitespace while preserving quoted literals."""
    if value is None:
        return None

    result: list[str] = []
    quote: str | None = None
    whitespace_pending = False
    index = 0

    while index < len(value):
        character = value[index]
        if quote is not None:
            result.append(character)
            if character == quote:
                if index + 1 < len(value) and value[index + 1] == quote:
                    result.append(value[index + 1])
                    index += 1
                else:
                    quote = None
            index += 1
            continue

        if character in {"'", '"'}:
            if whitespace_pending and result:
                result.append(" ")
            whitespace_pending = False
            quote = character
            result.append(character)
        elif character.isspace():
            whitespace_pending = True
        else:
            if whitespace_pending and result:
                result.append(" ")
            whitespace_pending = False
            result.append(character)
        index += 1

    return "".join(result).strip()


def render_contract(contract: dict[str, Any]) -> str:
    """Return the canonical, byte-stable JSON representation."""
    return json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _find_psql() -> str:
    configured = os.environ.get("PSQL")
    if configured and Path(configured).is_file():
        return configured

    discovered = shutil.which("psql")
    if discovered:
        return discovered

    candidates = sorted(
        glob.glob("C:/Program Files/PostgreSQL/*/bin/psql.exe"), reverse=True
    )
    if candidates:
        return candidates[0]
    raise RuntimeError("PostgreSQL psql client was not found")


def _psql_environment() -> dict[str, str]:
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))
    from app.core.config import DATABASE_URL

    parsed = urlsplit(DATABASE_URL)
    database_name = unquote(parsed.path.lstrip("/"))
    if database_name != EXPECTED_DATABASE:
        raise RuntimeError(
            f"Schema export aborted: expected database {EXPECTED_DATABASE!r}, "
            f"received {database_name!r}"
        )

    environment = os.environ.copy()
    environment.update(
        {
            "PGHOST": parsed.hostname or "localhost",
            "PGPORT": str(parsed.port or 5432),
            "PGDATABASE": database_name,
            "PGUSER": unquote(parsed.username or ""),
            "PGPASSWORD": unquote(parsed.password or ""),
            "PGAPPNAME": "bhavani_schema_contract_export",
            "PGOPTIONS": "-c default_transaction_read_only=on",
        }
    )
    query_options = parse_qs(parsed.query)
    if "sslmode" in query_options:
        environment["PGSSLMODE"] = query_options["sslmode"][-1]
    return environment


SECTION_PREFIX = "__BHAVANI_SCHEMA_CONTRACT__"
SNAPSHOT_QUERIES = (
    ("provenance", PROVENANCE_SQL, "database_name"),
    ("tables", TABLES_SQL, "table_name"),
    ("columns", COLUMNS_SQL, "table_name, ordinal_position"),
    ("primary_keys", PRIMARY_KEYS_SQL, "table_name, constraint_name"),
    ("foreign_keys", FOREIGN_KEYS_SQL, "table_name, constraint_name"),
    (
        "unique_constraints",
        UNIQUE_CONSTRAINTS_SQL,
        "table_name, constraint_name",
    ),
    ("check_constraints", CHECK_CONSTRAINTS_SQL, "table_name, constraint_name"),
    ("indexes", INDEXES_SQL, "table_name, index_name"),
    ("sequences", SEQUENCES_SQL, "sequence_name, owned_by_table"),
    ("enums", ENUMS_SQL, "enum_name"),
    ("catalog_counts", CATALOG_COUNTS_SQL, "application_tables"),
)


def _query_error_guard() -> str:
    return f"""\\if :ERROR
ROLLBACK;
\\set ON_ERROR_STOP on
SELECT 1 / 0;
\\endif
"""


def _labelled_json_query(label: str, inner_sql: str, order: str) -> str:
    return f"""
SELECT
    '{SECTION_PREFIX}{label}:' ||
    COALESCE(
        json_agg(row_to_json(contract_row) ORDER BY {order}),
        '[]'::json
    )::text
FROM (
{inner_sql.strip()}
) AS contract_row;
{_query_error_guard()}"""


def _snapshot_script() -> str:
    sections = "".join(
        _labelled_json_query(label, query, order)
        for label, query, order in SNAPSHOT_QUERIES
    )
    return f"""\\set ON_ERROR_STOP off
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
{_query_error_guard()}SELECT
    current_database() = '{EXPECTED_DATABASE}' AS database_ok,
    current_setting('transaction_read_only') = 'on' AS read_only_ok
\\gset contract_
{_query_error_guard()}\\if :contract_database_ok
\\else
ROLLBACK;
\\echo Schema export aborted: unexpected database
\\set ON_ERROR_STOP on
SELECT 1 / 0;
\\endif
\\if :contract_read_only_ok
\\else
ROLLBACK;
\\echo Schema export aborted: transaction is not read only
\\set ON_ERROR_STOP on
SELECT 1 / 0;
\\endif
{sections}ROLLBACK;
{_query_error_guard()}"""


def _parse_snapshot_output(output: str) -> dict[str, list[dict[str, Any]]]:
    expected_labels = {label for label, _, _ in SNAPSHOT_QUERIES}
    sections: dict[str, list[dict[str, Any]]] = {}

    for output_line in output.splitlines():
        line = output_line.strip()
        if not line:
            continue
        if not line.startswith(SECTION_PREFIX):
            raise RuntimeError("Read-only schema query returned unlabelled output")
        label_and_value = line[len(SECTION_PREFIX) :]
        label, separator, encoded_value = label_and_value.partition(":")
        if not separator or label not in expected_labels or label in sections:
            raise RuntimeError("Read-only schema query returned invalid section labels")
        value = json.loads(encoded_value)
        if not isinstance(value, list):
            raise RuntimeError(f"Schema contract section {label!r} is not a JSON array")
        sections[label] = value

    if set(sections) != expected_labels:
        missing = sorted(expected_labels - set(sections))
        extra = sorted(set(sections) - expected_labels)
        raise RuntimeError(
            f"Read-only schema result sections differ: missing={missing}, extra={extra}"
        )
    return sections


def _run_snapshot(
    psql: str, environment: dict[str, str]
) -> dict[str, list[dict[str, Any]]]:
    result = subprocess.run(
        [
            psql,
            "--no-psqlrc",
            "--quiet",
            "--no-align",
            "--tuples-only",
            "--file=-",
        ],
        input=_snapshot_script(),
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Read-only schema snapshot failed: {message}")
    return _parse_snapshot_output(result.stdout)


def _group_by_table(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        table_name = row.pop("table_name")
        grouped[table_name].append(row)
    return grouped


def _build_contract(
    sections: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    provenance_rows = sections["provenance"]
    if len(provenance_rows) != 1:
        raise RuntimeError("Expected exactly one provenance row")
    provenance = provenance_rows[0]
    if provenance["database_name"] != EXPECTED_DATABASE:
        raise RuntimeError("Schema export database verification failed")
    if provenance["transaction_read_only"] != "on":
        raise RuntimeError("Schema export transaction was not read only")

    table_rows = sections["tables"]
    table_names = [row["table_name"] for row in table_rows]
    if set(table_names) != EXPECTED_TABLES or len(table_names) != len(EXPECTED_TABLES):
        missing = sorted(EXPECTED_TABLES - set(table_names))
        extra = sorted(set(table_names) - EXPECTED_TABLES)
        raise RuntimeError(
            f"Application table manifest mismatch: missing={missing}, extra={extra}"
        )

    columns = _group_by_table(sections["columns"])
    primary_keys = _group_by_table(sections["primary_keys"])
    foreign_keys = _group_by_table(sections["foreign_keys"])
    unique_constraints = _group_by_table(sections["unique_constraints"])
    check_constraints = _group_by_table(sections["check_constraints"])
    indexes = _group_by_table(sections["indexes"])
    sequences = sections["sequences"]
    enums = sections["enums"]

    tables: list[dict[str, Any]] = []
    for table_name in sorted(table_names):
        table_columns = columns[table_name]
        for column in table_columns:
            column["server_default"] = normalize_sql_expression(
                column["server_default"]
            )
            column["generation_expression"] = normalize_sql_expression(
                column["generation_expression"]
            )

        table_checks = check_constraints[table_name]
        for check in table_checks:
            check["expression"] = normalize_sql_expression(check["expression"])

        table_indexes = indexes[table_name]
        primary_key_rows = primary_keys[table_name]
        if len(primary_key_rows) != 1:
            raise RuntimeError(
                f"Expected one primary key for {table_name}, found {len(primary_key_rows)}"
            )
        primary_key = primary_key_rows[0]
        primary_columns = primary_key["columns"]
        for index in table_indexes:
            index["predicate"] = normalize_sql_expression(index["predicate"])
            index["key_expressions"] = [
                normalize_sql_expression(expression)
                for expression in index["key_expressions"]
            ]
            index["redundant_primary_key_columns"] = bool(
                not index["primary"]
                and index["predicate"] is None
                and not index["included_columns"]
                and index["key_expressions"] == primary_columns
            )
            if index["primary"]:
                index["category"] = "primary_key_backed"
            elif index["constraint_type"] == "u":
                index["category"] = "unique_constraint_backed"
            elif index["unique"]:
                index["category"] = "other_unique"
            else:
                index["category"] = "nonunique_secondary"

        tables.append(
            {
                "name": table_name,
                "columns": table_columns,
                "primary_key": primary_key,
                "foreign_keys": foreign_keys[table_name],
                "unique_constraints": unique_constraints[table_name],
                "check_constraints": table_checks,
                "indexes": table_indexes,
            }
        )

    if len(sections["catalog_counts"]) != 1:
        raise RuntimeError("Expected exactly one independent catalog-count row")
    raw_counts = sections["catalog_counts"][0]
    index_counts = {
        "total_physical": raw_counts.pop("total_physical_indexes"),
        "primary_key_backed": raw_counts.pop("primary_key_backed_indexes"),
        "unique_constraint_backed": raw_counts.pop(
            "unique_constraint_backed_indexes"
        ),
        "other_unique": raw_counts.pop("other_unique_indexes"),
        "nonunique_secondary": raw_counts.pop("nonunique_secondary_indexes"),
        "redundant_primary_key_columns": raw_counts.pop(
            "redundant_primary_key_column_indexes"
        ),
    }
    catalog_counts = {**raw_counts, "indexes": index_counts}

    contract = {
        "format_version": FORMAT_VERSION,
        "provenance": {
            "database_name": provenance["database_name"],
            "postgresql_server_version": provenance["postgresql_server_version"],
            "source_alembic_revision": provenance["alembic_revision"],
        },
        "application_table_count": len(tables),
        "catalog_counts": catalog_counts,
        "tables": tables,
        "sequences": sequences,
        "enums": enums,
    }
    _validate_contract_counts(contract)
    return contract


def _validate_contract_counts(contract: dict[str, Any]) -> None:
    tables = contract["tables"]
    counts = contract["catalog_counts"]
    indexes = [index for table in tables for index in table["indexes"]]

    observed = {
        "application_tables": len(tables),
        "columns": sum(len(table["columns"]) for table in tables),
        "primary_keys": len(tables),
        "tables_with_exactly_one_primary_key": sum(
            1 for table in tables if table["primary_key"]
        ),
        "foreign_keys": sum(len(table["foreign_keys"]) for table in tables),
        "unique_constraints": sum(
            len(table["unique_constraints"]) for table in tables
        ),
        "check_constraints": sum(
            len(table["check_constraints"]) for table in tables
        ),
        "sequences": len(contract["sequences"]),
        "enums": len(contract["enums"]),
    }
    for name, value in observed.items():
        if counts[name] != value:
            raise RuntimeError(
                f"Independent catalog count mismatch for {name}: "
                f"catalog={counts[name]}, exported={value}"
            )

    observed_index_counts = {
        "total_physical": len(indexes),
        "primary_key_backed": sum(
            index["category"] == "primary_key_backed" for index in indexes
        ),
        "unique_constraint_backed": sum(
            index["category"] == "unique_constraint_backed" for index in indexes
        ),
        "other_unique": sum(
            index["category"] == "other_unique" for index in indexes
        ),
        "nonunique_secondary": sum(
            index["category"] == "nonunique_secondary" for index in indexes
        ),
        "redundant_primary_key_columns": sum(
            index["redundant_primary_key_columns"] for index in indexes
        ),
    }
    if counts["indexes"] != observed_index_counts:
        raise RuntimeError(
            "Independent physical-index counts do not match exported indexes: "
            f"catalog={counts['indexes']}, exported={observed_index_counts}"
        )
    classified = sum(
        counts["indexes"][category]
        for category in (
            "primary_key_backed",
            "unique_constraint_backed",
            "other_unique",
            "nonunique_secondary",
        )
    )
    if classified != counts["indexes"]["total_physical"]:
        raise RuntimeError("Physical-index category counts do not reconcile")


def export_contract() -> dict[str, Any]:
    psql = _find_psql()
    environment = _psql_environment()
    return _build_contract(_run_snapshot(psql, environment))


def export_to_path(output_path: Path) -> dict[str, Any]:
    contract = export_contract()
    rendered = render_contract(contract)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            dir=output_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_file.write(rendered)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, output_path)
    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return contract


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination JSON file",
    )
    arguments = parser.parse_args()

    contract = export_to_path(arguments.output)
    print(
        f"Exported {contract['application_table_count']} application tables "
        f"from {EXPECTED_DATABASE}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
