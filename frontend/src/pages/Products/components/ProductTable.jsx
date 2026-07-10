import {
  PencilSquareIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";

import { deleteProduct } from "../../../services/productService";

export default function ProductTable({
  products,
  loadProducts,
  setEditingProduct,
}) {
  const handleDelete = async (id) => {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this product?"
    );

    if (!confirmDelete) return;

    try {
      await deleteProduct(id);
      loadProducts();
    } catch (err) {
      console.error(err);
      alert("Failed to delete product");
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-5 mt-6 overflow-x-auto">

      <h2 className="text-2xl font-bold text-blue-700 mb-5">
        Products
      </h2>

      <table className="w-full border-collapse">

        <thead className="bg-blue-50">

          <tr>

            <th className="border p-3">School</th>

            <th className="border p-3">Category</th>

            <th className="border p-3">Product</th>

            <th className="border p-3">Size</th>

            <th className="border p-3">Color</th>

            <th className="border p-3">Price</th>

            <th className="border p-3">Stock</th>

            <th className="border p-3">Actions</th>

          </tr>

        </thead>

        <tbody>

          {products.length === 0 ? (

            <tr>

              <td
                colSpan="8"
                className="text-center p-6 text-gray-500"
              >
                No Products Found
              </td>

            </tr>

          ) : (

            products.map((product) => (

              <tr key={product.id}>

                <td className="border p-2">
                  {product.school}
                </td>

                <td className="border p-2">
                  {product.category}
                </td>

                <td className="border p-2 font-medium">
                  {product.product_name}
                </td>

                <td className="border p-2">
                  {product.size}
                </td>

                <td className="border p-2">
                  {product.color}
                </td>

                <td className="border p-2">
                  ₹{product.selling_price}
                </td>

                <td
                  className={`border p-2 font-semibold ${
                    product.stock <= 5
                      ? "text-red-600"
                      : "text-green-600"
                  }`}
                >
                  {product.stock}
                </td>

                <td className="border p-2">

                  <div className="flex justify-center gap-3">

                    <button
                      onClick={() =>
                        setEditingProduct(product)
                      }
                    >
                      <PencilSquareIcon className="h-6 w-6 text-blue-600 hover:text-blue-800" />
                    </button>

                    <button
                      onClick={() =>
                        handleDelete(product.id)
                      }
                    >
                      <TrashIcon className="h-6 w-6 text-red-600 hover:text-red-800" />
                    </button>

                  </div>

                </td>

              </tr>

            ))

          )}

        </tbody>

      </table>

    </div>
  );
}