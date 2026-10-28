"""Add original receipt identity fields to bills created after this revision.

Revision ID: c8f0a2d4e6b1
Revises: b2e4f8a1c3d5

Older bills deliberately retain NULL: current customer and catalog data cannot
reliably reconstruct what was printed when those bills were created.
"""

from alembic import op
import sqlalchemy as sa


revision = "c8f0a2d4e6b1"
down_revision = "b2e4f8a1c3d5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "bills",
        sa.Column("receipt_customer_name", sa.String(200), nullable=True),
        schema="public",
    )
    op.add_column(
        "bills",
        sa.Column("receipt_customer_phone", sa.String(15), nullable=True),
        schema="public",
    )
    op.add_column(
        "bill_items",
        sa.Column("receipt_sku", sa.String(100), nullable=True),
        schema="public",
    )


def downgrade():
    raise RuntimeError(
        "Receipt identity snapshots must not be deleted by a downgrade."
    )
