import { useBilling } from "../../../context/BillingContext";

export default function TotalsCard() {
  const { state } = useBilling();

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">

      <h2 className="text-2xl font-bold text-blue-700 mb-6">
        Bill Summary
      </h2>

      <div className="space-y-5">

        <div className="flex justify-between text-lg border-b pb-3">
          <span className="text-gray-600">Subtotal</span>

          <span className="font-semibold">
            ₹ {Number(state.subtotal).toFixed(2)}
          </span>
        </div>

        <div className="flex justify-between text-lg border-b pb-3">
          <span className="text-gray-600">Discount</span>

          <span className="font-semibold text-red-600">
            ₹ {Number(state.billDiscount).toFixed(2)}
          </span>
        </div>

        <div className="flex justify-between text-2xl font-bold border-b pb-4">

          <span>Grand Total</span>

          <span className="text-green-700">
            ₹ {Number(state.grandTotal).toFixed(2)}
          </span>

        </div>

        <div className="flex justify-between text-lg">

          <span className="text-gray-600">
            Paid
          </span>

          <span>
            ₹ {Number(state.paidAmount).toFixed(2)}
          </span>

        </div>

        <div className="flex justify-between text-xl font-bold">

          <span>
            Balance
          </span>

          <span className="text-red-600">
            ₹ {Number(state.balance).toFixed(2)}
          </span>

        </div>

      </div>

    </div>
  );
}