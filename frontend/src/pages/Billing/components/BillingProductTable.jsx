import { useState } from "react";
import { Trash2 } from "lucide-react";

import { useBilling } from "../../../context/BillingContext";
import { getProductVariants } from "../../../services/productService";

export default function BillingProductTable() {
  const { state, dispatch } = useBilling();

  const [variantCache, setVariantCache] = useState({});

  // ==========================
  // Load variants only once
  // ==========================
  const loadVariants = async (item) => {
    const key = `${item.product_name}_${item.school}_${item.category}`;

    if (variantCache[key]) return variantCache[key];

    try {
      const variants = await getProductVariants(
        item.product_name,
        item.school,
        item.category
      );

      setVariantCache((prev) => ({
        ...prev,
        [key]: variants,
      }));

      return variants;
    } catch (err) {
      console.error(err);
      return [];
    }
  };

  // ==========================
  // Increase Qty
  // ==========================
  const increaseQty = (item) => {
    dispatch({
      type: "UPDATE_ITEM_QTY",
      payload: {
        id: item.id,
        qty: item.qty + 1,
      },
    });
  };

  // ==========================
  // Decrease Qty
  // ==========================
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

  // ==========================
  // Delete Item
  // ==========================
  const removeItem = (id) => {
    dispatch({
      type: "REMOVE_ITEM",
      payload: id,
    });
  };

  // ==========================
  // Change Status
  // ==========================
  const changeStatus = (item, status) => {
    dispatch({
      type: "UPDATE_ITEM_STATUS",
      payload: {
        id: item.id,
        status,
      },
    });
  };

  // ==========================
  // Change Size
  // ==========================
  const changeSize = async (item, size) => {
    const variants = await loadVariants(item);

    const selected = variants.find(
      (v) => v.size === size
    );

    if (!selected) return;

    dispatch({
      type: "UPDATE_ITEM_SIZE",
      payload: {
        oldId: item.id,

        newItem: {
          ...item,

          id: selected.id,

          barcode: selected.barcode,

          sku: selected.sku,

          size: selected.size,

          color: selected.color,

          price: Number(selected.selling_price),

          stock: selected.stock,
        },
      },
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-5 overflow-x-auto">

      <h2 className="text-xl font-bold mb-4 text-blue-700">
        Billing Items
      </h2>

      <table className="min-w-full border-collapse">

        <thead className="bg-blue-50">

          <tr>

            <th className="border p-2">#</th>

            <th className="border p-2 text-left">
              Product
            </th>

            <th className="border p-2">
              Size
            </th>

            <th className="border p-2">
              Qty
            </th>

            <th className="border p-2">
              Price
            </th>

            <th className="border p-2">
              Amount
            </th>

            <th className="border p-2">
              Status
            </th>

            <th className="border p-2">
              Action
            </th>

          </tr>

        </thead>

        <tbody>

          {state.items.length === 0 ? (

            <tr>

              <td
                colSpan={8}
                className="text-center p-8 text-gray-500"
              >
                No Products Added
              </td>

            </tr>

          ) : (

            state.items.map((item, index) => {

              const key = `${item.product_name}_${item.school}_${item.category}`;

              const variants =
                variantCache[key] || [];

              const amount =
                item.qty * item.price;
                              return (

                <tr key={`${item.id}_${index}`}>

                  <td className="border p-2 text-center">
                    {index + 1}
                  </td>

                  {/* Product */}

                  <td className="border p-2">

                    <div className="font-semibold">
                      {item.product_name}
                    </div>

                    <div className="text-xs text-gray-500">
                      {item.barcode}
                    </div>

                  </td>

                  {/* Size */}

                  <td className="border p-2">

                    <select
                      value={item.size}
                      onFocus={() => loadVariants(item)}
                      onChange={(e) =>
                        changeSize(item, e.target.value)
                      }
                      className="border rounded p-1 w-full"
                    >

                      {variants.length === 0 ? (

                        <option>
                          {item.size}
                        </option>

                      ) : (

                        variants.map((variant) => (

                          <option
                            key={variant.id}
                            value={variant.size}
                            disabled={variant.stock <= 0}
                          >
                            {variant.size}
                            {variant.stock <= 0
                              ? " (Out)"
                              : ""}
                          </option>

                        ))

                      )}

                    </select>

                  </td>

                  {/* Quantity */}

                  <td className="border p-2">

                    <div className="flex justify-center items-center gap-2">

                      <button
                        onClick={() => decreaseQty(item)}
                        className="bg-red-500 hover:bg-red-600 text-white w-8 h-8 rounded"
                      >
                        -
                      </button>

                      <span className="font-bold">
                        {item.qty}
                      </span>

                      <button
                        onClick={() => increaseQty(item)}
                        className="bg-green-500 hover:bg-green-600 text-white w-8 h-8 rounded"
                      >
                        +
                      </button>

                    </div>

                  </td>

                  {/* Price */}

                  <td className="border p-2 text-center">

                    ₹ {Number(item.price).toFixed(2)}

                  </td>

                  {/* Amount */}

                  <td className="border p-2 text-center font-bold text-green-700">

                    ₹ {Number(amount).toFixed(2)}

                  </td>

                  {/* Status */}

                  <td className="border p-2">

                    <select
                      value={item.status || "Delivered"}
                      onChange={(e) =>
                        changeStatus(
                          item,
                          e.target.value
                        )
                      }
                      className="border rounded p-1 w-full"
                    >

                      <option value="Delivered">
                        Delivered
                      </option>

                      <option value="Pending">
                        Pending
                      </option>

                    </select>

                  </td>

                  {/* Delete */}

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