export default function PaymentPanel() {
  return (
    <div className="bg-white rounded-lg shadow p-5">
      <h2 className="text-xl font-bold mb-4">Payment</h2>

      <input
        type="number"
        placeholder="Paid Amount"
        className="w-full border rounded-lg p-2 mb-3"
      />

      <select className="w-full border rounded-lg p-2">
        <option>Cash</option>
        <option>UPI</option>
        <option>Card</option>
        <option>Credit</option>
      </select>
    </div>
  );
}