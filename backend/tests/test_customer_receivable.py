import unittest
from decimal import Decimal

from app.services.customer_receivable import (
    calculate_bill_receivable,
)


class CalculateBillReceivableTests(unittest.TestCase):
    def assert_state(
        self,
        original_total,
        payments,
        completed_returns,
        effective_obligation,
        due,
        refundable_entitlement,
        payment_status,
    ):
        state = calculate_bill_receivable(
            original_total=original_total,
            payments=payments,
            completed_returns=completed_returns,
        )

        self.assertEqual(
            state.effective_obligation,
            Decimal(str(effective_obligation)),
        )
        self.assertEqual(state.due, Decimal(str(due)))
        self.assertEqual(
            state.refundable_entitlement,
            Decimal(str(refundable_entitlement)),
        )
        self.assertEqual(state.payment_status, payment_status)

    def test_unpaid_bill_after_return(self):
        self.assert_state(
            1000,
            0,
            300,
            700,
            700,
            0,
            "Pending",
        )

    def test_partially_paid_bill_after_return(self):
        self.assert_state(
            1000,
            500,
            300,
            700,
            200,
            0,
            "Partial",
        )

    def test_fully_paid_bill_after_partial_return(self):
        self.assert_state(
            1000,
            1000,
            300,
            700,
            0,
            300,
            "Paid",
        )

    def test_fully_paid_bill_after_full_return(self):
        self.assert_state(
            1000,
            1000,
            1000,
            0,
            0,
            1000,
            "Paid",
        )

    def test_return_above_bill_total_is_allowed(self):
        self.assert_state(
            1000,
            0,
            1200,
            0,
            0,
            0,
            "Paid",
        )

    def test_negative_values_are_rejected(self):
        cases = (
            (Decimal("-0.01"), 0, 0),
            (1000, Decimal("-0.01"), 0),
            (1000, 0, Decimal("-0.01")),
        )

        for values in cases:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    calculate_bill_receivable(*values)

    def test_non_finite_values_are_rejected(self):
        cases = (
            (Decimal("NaN"), 0, 0),
            (1000, Decimal("Infinity"), 0),
            (1000, 0, Decimal("-Infinity")),
        )

        for values in cases:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    calculate_bill_receivable(*values)


if __name__ == "__main__":
    unittest.main()
