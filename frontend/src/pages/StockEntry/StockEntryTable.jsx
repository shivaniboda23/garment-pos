import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";

import { getProducts } from "../../services/productService";

export default function StockEntryTable({
  source,
  items,
  setItems,
}) {
  const [products, setProducts] = useState([]);

  const [search, setSearch] = useState("");

  // =====================================
  // LOAD PRODUCTS
  // =====================================

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      const data = await getProducts();

      setProducts(data);

    } catch (err) {

      console.error(err);

    }
  };

  // =====================================
  // SEARCH PRODUCTS
  // =====================================

  const filteredProducts = products.filter((product) => {

    if (!search.trim()) return true;

    return (

      product.product_name
        .toLowerCase()
        .includes(search.toLowerCase())

      ||

      product.barcode
        ?.toLowerCase()
        .includes(search.toLowerCase())

      ||

      product.sku
        ?.toLowerCase()
        .includes(search.toLowerCase())

    );

  });

  // =====================================
  // ADD PRODUCT
  // =====================================

  const addProduct = (product) => {

    const alreadyExists = items.find(
      (item) =>
        item.product_id === product.id
    );

    if (alreadyExists) {

      alert("Product already added.");

      return;

    }

    setItems([

      ...items,

      {

        product_id: product.id,

        barcode: product.barcode,

        sku: product.sku,

        product_name: product.product_name,

        school: product.school,

        category: product.category,

        size: product.size,

        color: product.color,

        qty: 1,

        cost_price:
          Number(product.purchase_price),

        source,

      },

    ]);

    setSearch("");

  };

  return (

    <div className="bg-white rounded-xl shadow-lg p-6">

      <h2 className="text-xl font-bold text-blue-700 mb-5">
        Add Products
      </h2>

      <input
        className="w-full border rounded-lg p-3 mb-5"
        placeholder="Search Product / Barcode / SKU..."
        value={search}
        onChange={(e) =>
          setSearch(e.target.value)
        }
      />

      <div className="border rounded-lg max-h-72 overflow-y-auto">

        {filteredProducts.length === 0 ? (

          <div className="p-5 text-center text-gray-500">

            No Products Found

          </div>

        ) : (

          filteredProducts.map((product) => (

            <div
              key={product.id}
              onClick={() => addProduct(product)}
              className="p-4 border-b cursor-pointer hover:bg-blue-50"
            >

              <div className="font-semibold">
                {product.product_name}
              </div>

              <div className="text-sm text-gray-500">
                {product.school}
              </div>

              <div className="flex justify-between mt-2">

                <span>
                  Size : {product.size}
                </span>

                <span className="font-semibold">

                  ₹ {Number(product.purchase_price).toFixed(2)}

                </span>

              </div>

            </div>

          ))

        )}

      </div>

      {/* ==========================
          STOCK TABLE
      ========================== */}

      <div className="mt-6 overflow-x-auto">

        <table className="min-w-full border-collapse">

          <thead className="bg-blue-50">

            <tr>

              <th className="border p-2">
                #
              </th>

              <th className="border p-2">
                Product
              </th>

              <th className="border p-2">
                Qty
              </th>

              <th className="border p-2">
                Cost Price
              </th>

              <th className="border p-2">
                Amount
              </th>

              <th className="border p-2">
                Action
              </th>

            </tr>

          </thead>

          <tbody>
            {items.length === 0 ? (

  <tr>

    <td
      colSpan={6}
      className="text-center p-8 text-gray-500"
    >
      No Products Added
    </td>

  </tr>

) : (

  items.map((item, index) => {

    const amount =
      Number(item.qty) *
      Number(item.cost_price);

    return (

      <tr key={`${item.product_id}_${item.size}`}>

        {/* ==========================
            SERIAL NO
        ========================== */}

        <td className="border p-2 text-center">

          {index + 1}

        </td>

        {/* ==========================
            PRODUCT
        ========================== */}

        <td className="border p-2">

          <div className="font-semibold">

            {item.product_name}

          </div>

          <div className="text-xs text-gray-500">

            {item.barcode}

          </div>

          <div className="text-xs text-blue-600">

            {item.size} ({source})

          </div>

        </td>

        {/* ==========================
            QUANTITY
        ========================== */}

        <td className="border p-2">

          <div className="flex justify-center items-center gap-2">

            <button
              className="bg-red-500 hover:bg-red-600 text-white w-8 h-8 rounded"
              onClick={() => {

                if (item.qty <= 1) return;

                const updated = [...items];

                updated[index].qty--;

                setItems(updated);

              }}
            >
              -
            </button>

            <span className="font-bold">

              {item.qty}

            </span>

            <button
              className="bg-green-500 hover:bg-green-600 text-white w-8 h-8 rounded"
              onClick={() => {

                const updated = [...items];

                updated[index].qty++;

                setItems(updated);

              }}
            >
              +
            </button>

          </div>

        </td>

        {/* ==========================
            COST PRICE
        ========================== */}

        <td className="border p-2">

          <input
            type="number"
            value={item.cost_price}
            className="border rounded w-24 p-2"
            onChange={(e) => {

              const updated = [...items];

              updated[index].cost_price =
                Number(e.target.value);

              setItems(updated);

            }}
          />

        </td>

        {/* ==========================
            AMOUNT
        ========================== */}

        <td className="border p-2 text-center font-bold text-green-700">

          ₹ {amount.toFixed(2)}

        </td>

        {/* ==========================
            DELETE
        ========================== */}

        <td className="border p-2 text-center">

          <button
            onClick={() => {

              setItems(

                items.filter(
                  (_, i) => i !== index
                )

              );

            }}
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

      {/* =====================================
          SUMMARY
      ===================================== */}

      <div className="mt-6 border-t pt-5">

        <div className="grid md:grid-cols-3 gap-4">

          {/* Total Products */}

          <div className="bg-blue-50 rounded-lg p-4">

            <div className="text-gray-600 text-sm">
              Products
            </div>

            <div className="text-2xl font-bold text-blue-700">

              {items.length}

            </div>

          </div>

          {/* Total Quantity */}

          <div className="bg-green-50 rounded-lg p-4">

            <div className="text-gray-600 text-sm">
              Total Qty
            </div>

            <div className="text-2xl font-bold text-green-700">

              {items.reduce(
                (sum, item) => sum + Number(item.qty),
                0
              )}

            </div>

          </div>

          {/* Grand Total */}

          <div className="bg-yellow-50 rounded-lg p-4">

            <div className="text-gray-600 text-sm">
              Total Cost
            </div>

            <div className="text-2xl font-bold text-orange-600">

              ₹{" "}

              {items
                .reduce(
                  (sum, item) =>
                    sum +
                    Number(item.qty) *
                      Number(item.cost_price),
                  0
                )
                .toFixed(2)}

            </div>

          </div>

        </div>

      </div>

    </div>

  );

}
