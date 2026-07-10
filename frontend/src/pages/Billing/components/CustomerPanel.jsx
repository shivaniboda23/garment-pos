import { useBilling } from "../../../context/BillingContext";

export default function CustomerPanel() {
  const { state, dispatch } = useBilling();

  const updateCustomer = (field, value) => {
    dispatch({
      type: "SET_CUSTOMER",
      payload: {
        [field]: value,
      },
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-5">

      <h2 className="text-xl font-bold text-blue-700 mb-5">
        Customer Details
      </h2>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">

        <input
          type="text"
          placeholder="Customer Name"
          value={state.customer.name}
          onChange={(e) =>
            updateCustomer("name", e.target.value)
          }
          className="border rounded-lg p-3"
        />

        <input
          type="text"
          placeholder="Mobile Number"
          value={state.customer.mobile}
          onChange={(e) =>
            updateCustomer("mobile", e.target.value)
          }
          className="border rounded-lg p-3"
        />

        <input
          type="text"
          placeholder="School / College"
          value={state.customer.school}
          onChange={(e) =>
            updateCustomer("school", e.target.value)
          }
          className="border rounded-lg p-3 bg-gray-50"
        />

        <input
          type="text"
          placeholder="Remarks"
          value={state.customer.remarks}
          onChange={(e) =>
            updateCustomer("remarks", e.target.value)
          }
          className="border rounded-lg p-3"
        />

      </div>

    </div>
  );
}