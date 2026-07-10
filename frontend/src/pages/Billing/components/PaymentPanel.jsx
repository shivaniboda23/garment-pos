import { useBilling } from "../../../context/BillingContext";

export default function PaymentPanel() {
  const { state, dispatch } = useBilling();

  const updatePaidAmount = (value) => {
    const paid = Number(value) || 0;

    dispatch({
      type: "SET_PAYMENT",
      payload: {
        paidAmount: paid,
        paymentMode: state.paymentMode,
        balance: state.grandTotal - paid,
      },
    });
  };

  const changeMode = (mode) => {
    dispatch({
      type: "SET_PAYMENT",
      payload: {
        paidAmount: state.paidAmount,
        paymentMode: mode,
        balance: state.grandTotal - state.paidAmount,
      },
    });
  };

  const modes = [
    "Cash",
    "UPI",
    "Card",
    "Credit",
  ];

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">

      <h2 className="text-2xl font-bold text-blue-700 mb-6">
        Payment
      </h2>

      <div className="grid grid-cols-2 gap-3 mb-6">

        {modes.map((mode) => (

          <button
            key={mode}
            onClick={() => changeMode(mode)}
            className={`p-3 rounded-lg border font-semibold transition

            ${
              state.paymentMode === mode
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-white hover:bg-gray-100"
            }`}
          >
            {mode}
          </button>

        ))}

      </div>

      <div className="space-y-5">

        <div>

          <label className="font-medium text-gray-700">
            Amount Paid
          </label>

          <input
            type="number"
            value={state.paidAmount}
            onChange={(e) => updatePaidAmount(e.target.value)}
            className="mt-2 w-full border rounded-lg p-3 text-lg"
          />

        </div>

        <div className="flex justify-between text-xl font-bold">

          <span>Balance</span>

          <span
            className={
              state.balance > 0
                ? "text-red-600"
                : "text-green-600"
            }
          >
            ₹ {Number(state.balance).toFixed(2)}
          </span>

        </div>

      </div>

    </div>
  );
}