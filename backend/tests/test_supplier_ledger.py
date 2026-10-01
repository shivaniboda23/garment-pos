import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

from fastapi import HTTPException

from app.crud.supplier_payment import (
    _sort_supplier_ledger_transactions,
    get_supplier_ledger,
)
from app.models.purchase import Purchase
from app.models.purchase_return import PurchaseReturn
from app.models.supplier import Supplier
from app.models.supplier_credit_application import (
    SupplierCreditApplication,
)
from app.models.supplier_payment import SupplierPayment
from app.schemas.supplier_payment import SupplierLedgerResponse


INDIA_TIMEZONE = timezone(
    timedelta(
        hours=5,
        minutes=30,
    )
)


def _transaction(
    date,
    transaction_type,
    priority,
    record_id,
):
    return {
        "date": date,
        "transaction_type": transaction_type,
        "priority": priority,
        "id": record_id,
    }


def _criterion_value(criterion):
    right = criterion.right

    if hasattr(right, "value"):
        return right.value

    rendered = str(right).lower()
    if rendered == "true":
        return True
    if rendered == "false":
        return False

    raise AssertionError(
        f"Unsupported fake-query criterion: {criterion}"
    )


class _FakeQuery:
    def __init__(
        self,
        rows,
    ):
        self.rows = list(rows)

    def filter(
        self,
        *criteria,
    ):
        for criterion in criteria:
            column_name = criterion.left.key
            expected = _criterion_value(criterion)
            comparison = criterion.operator
            self.rows = [
                row
                for row in self.rows
                if comparison(
                    getattr(row, column_name),
                    expected,
                )
            ]

        return self

    def order_by(
        self,
        *clauses,
    ):
        return self

    def first(self):
        if not self.rows:
            return None
        return self.rows[0]

    def all(self):
        return list(self.rows)


class _FakeSession:
    def __init__(
        self,
        rows_by_model,
    ):
        self.rows_by_model = rows_by_model

    def query(
        self,
        *entities,
    ):
        if len(entities) != 1:
            raise AssertionError(
                f"Unexpected fake query entities: {entities}"
            )

        model = entities[0]
        if model not in self.rows_by_model:
            raise AssertionError(
                f"Unexpected fake query model: {model}"
            )

        return _FakeQuery(
            self.rows_by_model[model],
        )


def _supplier(
    *,
    supplier_id=3,
    shop_id=3,
    is_active=True,
    opening_balance=Decimal("10.00"),
):
    return SimpleNamespace(
        id=supplier_id,
        shop_id=shop_id,
        is_active=is_active,
        supplier_name="Test Supplier",
        opening_balance=opening_balance,
    )


def _accounting(
    *,
    payable=Decimal("60.00"),
    supplier_credit=Decimal("0.00"),
    net_position=Decimal("60.00"),
):
    return SimpleNamespace(
        payable=payable,
        unallocated_credit=supplier_credit,
        net_position=net_position,
    )


class SupplierLedgerSortTests(unittest.TestCase):
    def test_mixed_datetimes_use_aware_comparison_timezone(self):
        aware = datetime(
            2026,
            1,
            1,
            10,
            0,
            tzinfo=INDIA_TIMEZONE,
        )
        naive = datetime(
            2026,
            1,
            1,
            9,
            30,
        )
        transactions = [
            _transaction(aware, "Purchase", 1, 1),
            _transaction(naive, "Purchase Return", 2, 2),
        ]
        original_dates = {
            transaction["id"]: transaction["date"]
            for transaction in transactions
        }

        _sort_supplier_ledger_transactions(
            transactions,
        )

        self.assertEqual(
            [2, 1],
            [transaction["id"] for transaction in transactions],
        )
        for transaction in transactions:
            self.assertIs(
                transaction["date"],
                original_dates[transaction["id"]],
            )
        self.assertIsNone(naive.tzinfo)
        self.assertEqual(
            timedelta(hours=5, minutes=30),
            aware.utcoffset(),
        )

    def test_all_aware_offsets_sort_by_actual_instant(self):
        first = datetime(
            2026,
            1,
            1,
            10,
            0,
            tzinfo=INDIA_TIMEZONE,
        )
        second = datetime(
            2026,
            1,
            1,
            4,
            45,
            tzinfo=timezone.utc,
        )
        third = datetime(
            2025,
            12,
            31,
            23,
            0,
            tzinfo=timezone(
                -timedelta(hours=6)
            ),
        )
        transactions = [
            _transaction(third, "Payment", 3, 3),
            _transaction(second, "Payment", 3, 2),
            _transaction(first, "Payment", 3, 1),
        ]

        _sort_supplier_ledger_transactions(
            transactions,
        )

        self.assertEqual(
            [1, 2, 3],
            [transaction["id"] for transaction in transactions],
        )

    def test_all_naive_datetimes_keep_wall_clock_order(self):
        transactions = [
            _transaction(
                datetime(2026, 1, 1, 12, 0),
                "Purchase",
                1,
                3,
            ),
            _transaction(
                datetime(2026, 1, 1, 9, 0),
                "Purchase",
                1,
                1,
            ),
            _transaction(
                datetime(2026, 1, 1, 10, 0),
                "Purchase",
                1,
                2,
            ),
        ]

        _sort_supplier_ledger_transactions(
            transactions,
        )

        self.assertEqual(
            [1, 2, 3],
            [transaction["id"] for transaction in transactions],
        )
        self.assertTrue(
            all(
                transaction["date"].tzinfo is None
                for transaction in transactions
            )
        )

    def test_equal_instants_use_priority_then_id(self):
        local_instant = datetime(
            2026,
            1,
            1,
            12,
            0,
            tzinfo=INDIA_TIMEZONE,
        )
        transactions = [
            _transaction(
                local_instant,
                "Purchase",
                1,
                9,
            ),
            _transaction(
                datetime(
                    2026,
                    1,
                    1,
                    8,
                    30,
                    tzinfo=timezone(
                        timedelta(hours=2)
                    ),
                ),
                "Credit Application",
                4,
                4,
            ),
            _transaction(
                datetime(
                    2026,
                    1,
                    1,
                    6,
                    30,
                    tzinfo=timezone.utc,
                ),
                "Payment",
                3,
                3,
            ),
            _transaction(
                datetime(2026, 1, 1, 12, 0),
                "Purchase Return",
                2,
                2,
            ),
        ]

        _sort_supplier_ledger_transactions(
            transactions,
        )

        self.assertEqual(
            [
                "Purchase",
                "Purchase Return",
                "Payment",
                "Credit Application",
            ],
            [
                transaction["transaction_type"]
                for transaction in transactions
            ],
        )

        same_type = [
            _transaction(
                local_instant,
                "Purchase",
                1,
                3,
            ),
            _transaction(
                datetime(
                    2026,
                    1,
                    1,
                    6,
                    30,
                    tzinfo=timezone.utc,
                ),
                "Purchase",
                1,
                1,
            ),
            _transaction(
                datetime(2026, 1, 1, 12, 0),
                "Purchase",
                1,
                2,
            ),
        ]

        _sort_supplier_ledger_transactions(
            same_type,
        )

        self.assertEqual(
            [1, 2, 3],
            [transaction["id"] for transaction in same_type],
        )


class SupplierLedgerCrudTests(unittest.TestCase):
    def _session(
        self,
        *,
        suppliers=None,
        purchases=None,
        purchase_returns=None,
        payments=None,
        credit_applications=None,
    ):
        return _FakeSession(
            {
                Supplier: suppliers or [],
                Purchase: purchases or [],
                PurchaseReturn: purchase_returns or [],
                SupplierPayment: payments or [],
                SupplierCreditApplication:
                    credit_applications or [],
            }
        )

    @mock.patch(
        "app.crud.supplier_payment.get_supplier_accounting"
    )
    def test_mixed_four_type_ledger_preserves_balances_and_dates(
        self,
        get_accounting,
    ):
        purchase_date = datetime(
            2026,
            1,
            1,
            10,
            0,
            tzinfo=INDIA_TIMEZONE,
        )
        return_date = datetime(
            2026,
            1,
            1,
            11,
            0,
        )
        payment_date = datetime(
            2026,
            1,
            1,
            6,
            0,
            tzinfo=timezone.utc,
        )
        application_date = datetime(
            2026,
            1,
            1,
            7,
            0,
            tzinfo=timezone.utc,
        )
        pending_date = datetime(
            2025,
            1,
            1,
            0,
            0,
        )
        session = self._session(
            suppliers=[
                _supplier(),
                _supplier(
                    supplier_id=4,
                    shop_id=4,
                ),
            ],
            purchases=[
                SimpleNamespace(
                    id=10,
                    shop_id=3,
                    supplier_id=3,
                    created_at=purchase_date,
                    invoice_number="P-10",
                    grand_total=Decimal("100.00"),
                ),
                SimpleNamespace(
                    id=11,
                    shop_id=4,
                    supplier_id=3,
                    created_at=purchase_date,
                    invoice_number="WRONG-SHOP",
                    grand_total=Decimal("999.00"),
                ),
                SimpleNamespace(
                    id=12,
                    shop_id=3,
                    supplier_id=4,
                    created_at=purchase_date,
                    invoice_number="WRONG-SUPPLIER",
                    grand_total=Decimal("999.00"),
                ),
            ],
            purchase_returns=[
                SimpleNamespace(
                    id=20,
                    shop_id=3,
                    supplier_id=3,
                    status="Completed",
                    created_at=return_date,
                    return_number="PR-20",
                    total_amount=Decimal("20.00"),
                ),
                SimpleNamespace(
                    id=21,
                    shop_id=3,
                    supplier_id=3,
                    status="Pending",
                    created_at=pending_date,
                    return_number="PENDING",
                    total_amount=Decimal("999.00"),
                ),
            ],
            payments=[
                SimpleNamespace(
                    id=30,
                    shop_id=3,
                    supplier_id=3,
                    payment_date=payment_date,
                    reference_number=None,
                    amount=Decimal("30.00"),
                ),
                SimpleNamespace(
                    id=31,
                    shop_id=4,
                    supplier_id=3,
                    payment_date=payment_date,
                    reference_number="WRONG-SHOP",
                    amount=Decimal("999.00"),
                ),
            ],
            credit_applications=[
                SimpleNamespace(
                    id=40,
                    shop_id=3,
                    supplier_id=3,
                    applied_at=application_date,
                    reference_number=None,
                    amount=Decimal("15.00"),
                ),
                SimpleNamespace(
                    id=41,
                    shop_id=3,
                    supplier_id=4,
                    applied_at=application_date,
                    reference_number="WRONG-SUPPLIER",
                    amount=Decimal("999.00"),
                ),
            ],
        )
        get_accounting.return_value = _accounting()

        result = get_supplier_ledger(
            db=session,
            shop_id=3,
            supplier_id=3,
        )

        entries = result["entries"]
        self.assertEqual(
            [
                "Purchase",
                "Purchase Return",
                "Payment",
                "Credit Application",
            ],
            [entry["transaction_type"] for entry in entries],
        )
        self.assertEqual(
            [
                Decimal("110.00"),
                Decimal("90.00"),
                Decimal("60.00"),
                Decimal("60.00"),
            ],
            [entry["balance"] for entry in entries],
        )
        self.assertEqual(
            [
                (Decimal("100.00"), Decimal("0.00")),
                (Decimal("0.00"), Decimal("20.00")),
                (Decimal("0.00"), Decimal("30.00")),
                (Decimal("15.00"), Decimal("15.00")),
            ],
            [
                (entry["debit"], entry["credit"])
                for entry in entries
            ],
        )
        expected_dates = (
            purchase_date,
            return_date,
            payment_date,
            application_date,
        )
        for entry, expected_date in zip(
            entries,
            expected_dates,
        ):
            self.assertIs(entry["date"], expected_date)

        self.assertEqual(
            {
                "supplier_id",
                "supplier_name",
                "opening_balance",
                "entries",
                "payable",
                "supplier_credit",
                "net_position",
                "transaction_outstanding",
            },
            set(result),
        )
        self.assertEqual(
            {
                "date",
                "transaction_type",
                "reference",
                "debit",
                "credit",
                "balance",
            },
            set(entries[0]),
        )
        response = SupplierLedgerResponse.model_validate(
            result,
        )
        self.assertEqual(4, len(response.entries))
        self.assertIsNone(
            response.entries[1].date.tzinfo
        )
        self.assertIsNotNone(
            response.entries[0].date.tzinfo
        )
        get_accounting.assert_called_once_with(
            db=session,
            shop_id=3,
            supplier_id=3,
            opening_balance=Decimal("10.00"),
        )

    @mock.patch(
        "app.crud.supplier_payment.get_supplier_accounting"
    )
    def test_empty_and_single_type_ledgers_remain_valid(
        self,
        get_accounting,
    ):
        get_accounting.return_value = _accounting(
            payable=Decimal("10.00"),
            net_position=Decimal("10.00"),
        )
        empty_session = self._session(
            suppliers=[_supplier()],
        )

        empty_result = get_supplier_ledger(
            db=empty_session,
            shop_id=3,
            supplier_id=3,
        )

        self.assertEqual([], empty_result["entries"])
        SupplierLedgerResponse.model_validate(
            empty_result,
        )

        return_date = datetime(
            2026,
            1,
            1,
            11,
            0,
        )
        single_session = self._session(
            suppliers=[_supplier()],
            purchase_returns=[
                SimpleNamespace(
                    id=20,
                    shop_id=3,
                    supplier_id=3,
                    status="Completed",
                    created_at=return_date,
                    return_number="PR-20",
                    total_amount=Decimal("3.00"),
                )
            ],
        )

        single_result = get_supplier_ledger(
            db=single_session,
            shop_id=3,
            supplier_id=3,
        )

        self.assertEqual(
            ["Purchase Return"],
            [
                entry["transaction_type"]
                for entry in single_result["entries"]
            ],
        )
        self.assertEqual(
            Decimal("7.00"),
            single_result["entries"][0]["balance"],
        )
        self.assertIs(
            return_date,
            single_result["entries"][0]["date"],
        )
        SupplierLedgerResponse.model_validate(
            single_result,
        )

    def test_missing_inactive_and_wrong_shop_supplier_remain_404(
        self,
    ):
        cases = {
            "missing": [],
            "inactive": [
                _supplier(is_active=False)
            ],
            "wrong_shop": [
                _supplier(shop_id=4)
            ],
        }

        for name, suppliers in cases.items():
            with self.subTest(name=name):
                session = self._session(
                    suppliers=suppliers,
                )

                with self.assertRaises(
                    HTTPException
                ) as context:
                    get_supplier_ledger(
                        db=session,
                        shop_id=3,
                        supplier_id=3,
                    )

                self.assertEqual(
                    404,
                    context.exception.status_code,
                )
                self.assertEqual(
                    "Supplier not found.",
                    context.exception.detail,
                )


if __name__ == "__main__":
    unittest.main()
