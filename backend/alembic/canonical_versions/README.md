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
