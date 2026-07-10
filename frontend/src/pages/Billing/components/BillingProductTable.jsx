import { Trash2 } from "lucide-react";
import { useBilling } from "../../../context/BillingContext";

export default function BillingProductTable() {
  const { state, dispatch } = useBilling();

  const increaseQty = (item) => {
    dispatch({
      type: "UPDATE_ITEM_QTY",
      payload: {
        id: item.id,
        qty: item.qty + 1,
      },
    });
  };

  const decreaseQty = (item) => {
    if (item.qty <= 1) return;

    dispatch({
      type: "UPDATE_ITEM_QTY",
      payload: {
        id: item.id,
        qty: item.qty - 1,
      },
    });
  };

  const removeItem = (id) => {
    dispatch({
      type: "REMOVE_ITEM",
      payload: id,
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-5 overflow-x-auto">

      <h2 className="text-xl font-bold mb-4 text-blue-700">
        Billing Items
      </h2>

      <table className="w-full">

        <thead className="bg-blue-50">

          <tr>
            <th className="border p-2">#</th>
            <th className="border p-2 text-left">Product</th>
            <th className="border p-2">Size</th>
            <th className="border p-2">Qty</th>
            <th className="border p-2">Price</th>
            <th className="border p-2">Total</th>
            <th className="border p-2">Action</th>
          </tr>

        </thead>

        <tbody>

          {state.items.length === 0 ? (
            <tr>
              <td
                colSpan={7}
                className="text-center p-8 text-gray-500"
              >
                No Products Added
              </td>
            </tr>
          ) : (
            state.items.map((item, index) => {

              const total = item.qty * item.price;

              return (
                <tr key={item.id}>

                  <td className="border p-2 text-center">
                    {index + 1}
                  </td>

                  <td className="border p-2">

                    <div className="font-semibold">
                      {item.product_name}
                    </div>

                    <div className="text-xs text-gray-500">
                      {item.barcode}
                    </div>

                  </td>

                  <td className="border p-2 text-center">
                    {item.size}
                  </td>

                  <td className="border p-2">

                    <div className="flex justify-center items-center gap-2">

                      <button
                        onClick={() => decreaseQty(item)}
                        className="bg-red-500 text-white w-8 h-8 rounded"
                      >
                        -
                      </button>

                      <span className="font-bold">
                        {item.qty}
                      </span>

                      <button
                        onClick={() => increaseQty(item)}
                        className="bg-green-500 text-white w-8 h-8 rounded"
                      >
                        +
                      </button>

                    </div>

                  </td>

                  <td className="border p-2 text-center">
                    ₹ {Number(item.price).toFixed(2)}
                  </td>

                  <td className="border p-2 text-center font-bold text-green-700">
                    ₹ {Number(total).toFixed(2)}
                  </td>

                  <td className="border p-2 text-center">

                    <button
                      onClick={() => removeItem(item.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 size={20} />
                    </button>

                  </td>

                </tr>
              );

            })
          )}

        </tbody>

      </table>

    </div>
  );
}