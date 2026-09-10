"""Compare a canonical live contract with a disposable-database export."""

from __future__ import annotations

import argparse
from copy import deepcopy
import difflib
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_REDUNDANT_INDEXES = {
    ("brands", "ix_brands_id"),
    ("categories", "ix_categories_id"),
    ("customers", "ix_customers_id"),
    ("product_variants", "ix_product_variants_id"),
    ("products", "ix_products_id"),
    ("sale_items", "ix_sale_items_id"),
    ("sales", "ix_sales_id"),
    ("shops", "ix_shops_id"),
    ("stocks", "ix_stocks_id"),
    ("users", "ix_users_id"),
}

TAILORING_STOCK_TYPE_CHECK = (
    "tailoring_jobs",
    "tailoring_jobs_stock_type_check",
)
TAILORING_STOCK_TYPE_CHECK_EXPRESSIONS = {
    "stock_type::text = ANY (ARRAY['K'::character varying, "
    "'R'::character varying]::text[])",
    "stock_type::text = ANY (ARRAY['K'::character varying::text, "
    "'R'::character varying::text])",
}
TAILORING_STOCK_TYPE_CHECK_CANONICAL = min(
    TAILORING_STOCK_TYPE_CHECK_EXPRESSIONS
)


def _reconciled_index_counts(contract: dict[str, Any]) -> dict[str, int]:
    indexes = [index for table in contract["tables"] for index in table["indexes"]]
    categories = (
        "primary_key_backed",
        "unique_constraint_backed",
        "other_unique",
        "nonunique_secondary",
    )
    return {
        "total_physical": len(indexes),
        **{
            category: sum(index["category"] == category for index in indexes)
            for category in categories
        },
        "redundant_primary_key_columns": sum(
            index["redundant_primary_key_columns"] for index in indexes
        ),
    }


def _normalize_column_ordinals(table: dict[str, Any]) -> None:
    """Validate physical ordering and replace sparse ordinals with list order."""
    previous_ordinal: int | None = None
    for dense_position, column in enumerate(table["columns"], start=1):
        ordinal = column.get("ordinal_position")
        if not isinstance(ordinal, int) or isinstance(ordinal, bool):
            raise ValueError(
                "Column ordinal_position must be an integer for "
                f"{table['name']}.{column.get('column_name', '<unknown>')}"
            )
        if previous_ordinal is not None and ordinal <= previous_ordinal:
            raise ValueError(
                "Column ordinal_position values must be strictly increasing for "
                f"table {table['name']!r}: {ordinal} follows {previous_ordinal}"
            )
        previous_ordinal = ordinal
        column["ordinal_position"] = dense_position


def _normalize_check_constraints(table: dict[str, Any]) -> None:
    """Normalize one verified PostgreSQL rendering equivalence."""
    for constraint in table["check_constraints"]:
        identity = (table["name"], constraint["constraint_name"])
        if (
            identity == TAILORING_STOCK_TYPE_CHECK
            and constraint["expression"] in TAILORING_STOCK_TYPE_CHECK_EXPRESSIONS
        ):
            constraint["expression"] = TAILORING_STOCK_TYPE_CHECK_CANONICAL


def normalized_contract(contract: dict[str, Any]) -> dict[str, Any]:
    """Normalize only reviewed, semantics-preserving contract differences."""
    normalized = deepcopy(contract)
    normalized["provenance"].pop("database_name", None)
    normalized["provenance"].pop("source_alembic_revision", None)

    for table in normalized["tables"]:
        _normalize_column_ordinals(table)
        _normalize_check_constraints(table)
        retained_indexes = []
        for index in table["indexes"]:
            identity = (table["name"], index["index_name"])
            if identity in ALLOWED_REDUNDANT_INDEXES:
                if not index["redundant_primary_key_columns"]:
                    raise ValueError(
                        f"Allowlisted index is not marked redundant: {identity}"
                    )
                continue
            if index["redundant_primary_key_columns"]:
                raise ValueError(f"Unexpected redundant index: {identity}")
            retained_indexes.append(index)
        table["indexes"] = retained_indexes

    normalized["catalog_counts"]["indexes"] = _reconciled_index_counts(normalized)
    return normalized


def compare_contracts(
    authoritative: dict[str, Any], candidate: dict[str, Any]
) -> list[str]:
    expected = json.dumps(
        normalized_contract(authoritative),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ).splitlines()
    actual = json.dumps(
        normalized_contract(candidate),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ).splitlines()
    return list(
        difflib.unified_diff(
            expected,
            actual,
            fromfile="authoritative-live-contract",
            tofile="disposable-database-contract",
            lineterm="",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authoritative", type=Path)
    parser.add_argument("candidate", type=Path)
    arguments = parser.parse_args()

    authoritative = json.loads(arguments.authoritative.read_text(encoding="utf-8"))
    candidate = json.loads(arguments.candidate.read_text(encoding="utf-8"))
    differences = compare_contracts(authoritative, candidate)
    if differences:
        print("\n".join(differences))
        return 1
    print("Schema contracts match under the approved comparison rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
