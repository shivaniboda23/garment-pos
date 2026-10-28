"""Receipt identity fields are additive and remain usable for legacy bills."""

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import String

from app.models.bill import Bill
from app.models.bill_item import BillItem
from app.schemas.billing import BillResponse


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "canonical_versions"
    / "c8f0a2d4e6b1_receipt_identity_snapshot.py"
)


class ReceiptIdentitySnapshotTests(unittest.TestCase):
    def test_model_fields_are_nullable_and_fit_source_lengths(self):
        for model, names in (
            (Bill, {"receipt_customer_name": 200, "receipt_customer_phone": 15}),
            (BillItem, {"receipt_sku": 100}),
        ):
            for name, length in names.items():
                column = model.__table__.c[name]
                self.assertTrue(column.nullable)
                self.assertIsInstance(column.type, String)
                self.assertEqual(length, column.type.length)

    def test_response_preserves_snapshot_values_without_live_relations(self):
        data = {
            "id": 5, "sale_id": 9, "invoice_number": "INV-5",
            "customer_id": 3, "receipt_customer_name": "Original Name",
            "receipt_customer_phone": "0000000000", "subtotal": "100.00",
            "discount": "0.00", "gst": "0.00", "grand_total": "100.00",
            "payment_method": "Cash", "payment_status": "Paid",
            "bill_status": "Completed", "remarks": None,
            "items": [{
                "id": 7, "variant_id": 8, "product_id": 2,
                "receipt_sku": "ORIGINAL-SKU", "ordered_qty": 1,
                "delivered_qty": 1, "pending_qty": 0,
                "k_quantity": 1, "r_quantity": 0,
                "k_delivered_qty": 1, "r_delivered_qty": 0,
                "selling_price": "100.00", "discount": "0.00",
                "gst_percentage": "0.00", "gst": "0.00",
                "total": "100.00", "item_status": "Delivered",
            }],
            "payments": [{"id": 1, "payment_method": "Cash", "amount": "100.00"}],
        }
        value = BillResponse.model_validate(data).model_dump(mode="json")
        self.assertEqual("Original Name", value["receipt_customer_name"])
        self.assertEqual("0000000000", value["receipt_customer_phone"])
        self.assertEqual("ORIGINAL-SKU", value["items"][0]["receipt_sku"])
        data.pop("receipt_customer_name")
        data.pop("receipt_customer_phone")
        data["items"][0].pop("receipt_sku")
        old = BillResponse.model_validate(data)
        self.assertIsNone(old.receipt_customer_name)
        self.assertIsNone(old.receipt_customer_phone)
        self.assertIsNone(old.items[0].receipt_sku)

    def test_migration_adds_nullable_fields_without_backfill(self):
        spec = importlib.util.spec_from_file_location("receipt_migration", MIGRATION)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual("b2e4f8a1c3d5", module.down_revision)
        with patch.object(module.op, "add_column") as add_column:
            module.upgrade()
        self.assertEqual(3, add_column.call_count)
        seen = {(call.args[0], call.args[1].name): call for call in add_column.call_args_list}
        self.assertEqual({
            ("bills", "receipt_customer_name"),
            ("bills", "receipt_customer_phone"),
            ("bill_items", "receipt_sku"),
        }, set(seen))
        for call in seen.values():
            self.assertEqual("public", call.kwargs["schema"])
            self.assertTrue(call.args[1].nullable)
        with self.assertRaisesRegex(RuntimeError, "must not be deleted"):
            module.downgrade()


if __name__ == "__main__":
    unittest.main()
