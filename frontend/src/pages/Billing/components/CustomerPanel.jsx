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
    <div className="bg-white rounded-2xl shadow-lg p-6">

      <h2 className="text-xl font-bold text-blue-700 mb-5">
        Customer Details
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

        <div>
          <label className="block text-sm font-medium mb-2">
            Customer Name
          </label>

          <input
            className="w-full border rounded-lg p-3 focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="Enter customer name"
            value={state.customer?.name || ""}
            onChange={(e) =>
              updateCustomer("name", e.target.value)
            }
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Mobile Number
          </label>

          <input
            className="w-full border rounded-lg p-3 focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="9876543210"
            value={state.customer?.mobile || ""}
            onChange={(e) =>
              updateCustomer("mobile", e.target.value)
            }
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            School
          </label>

          <input
            className="w-full border rounded-lg p-3 bg-gray-100"
            value={state.selectedSchool || "Not Selected"}
            readOnly
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Remarks
          </label>

          <input
            className="w-full border rounded-lg p-3 focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="Optional remarks"
            value={state.customer?.remarks || ""}
            onChange={(e) =>
              updateCustomer("remarks", e.target.value)
            }
          />
        </div>

      </div>

    </div>
  );
}