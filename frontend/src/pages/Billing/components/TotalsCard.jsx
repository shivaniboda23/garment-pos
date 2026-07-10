import { useBilling } from "../../../context/BillingContext";

export default function TotalsCard() {
  const { state } = useBilling();

  return (
    <div className="bg-white rounded-xl shadow-lg p-5">
      <h2 className="text-xl font-bold mb-4 text-blue-700">
        Bill Summary
      </h2>

      <div className="space-y-3">

        <div className="flex justify-between border-b pb-2">
          <span>Subtotal</span>
          <span>₹ {Number(state.subtotal || 0).toFixed(2)}</span>
        </div>

        <div className="flex justify-between border-b pb-2">
          <span>Bill Discount</span>
          <span>₹ {Number(state.billDiscount || 0).toFixed(2)}</span>
        </div>

        <div className="flex justify-between border-b pb-2">
          <span>Round Off</span>
          <span>₹ {Number(state.roundOff || 0).toFixed(2)}</span>
        </div>

        <div className="flex justify-between text-2xl font-bold text-green-700 pt-3">
          <span>Grand Total</span>
          <span>₹ {Number(state.grandTotal || 0).toFixed(2)}</span>
        </div>

      </div>
    </div>
  );
}