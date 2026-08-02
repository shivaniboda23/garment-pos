import { useEffect, useState } from "react";
import axios from "axios";
import {
  addProduct,
  updateProduct,
} from "../../../services/productService";

const categories = [
  "Uniform",
  "Sports",
  "Shoes",
  "Books",
  "Accessories",
  "Other",
];

export default function ProductForm({
  loadProducts,
  editingProduct,
  setEditingProduct,
}) {
  const [schools, setSchools] = useState([]);

  const initialForm = {
    barcode: "",
    sku: "",
    school: "",
    category: "",
    product_name: "",
    size: [],
    color: "",
    purchase_price: "",
    selling_price: "",
    mrp: "",
    stock: "",
    remarks: "",
  };

  const [form, setForm] = useState(initialForm);

  useEffect(() => {
    loadSchools();
  }, []);

  useEffect(() => {
    if (editingProduct) {
      setForm({
        ...initialForm,
        ...editingProduct,
      });
    }
  }, [editingProduct]);

  const loadSchools = async () => {
    try {
      const res = await axios.get(
        "http://localhost:5000/api/schools"
      );

      setSchools(res.data);
    } catch (err) {
      console.log(err);
    }
  };

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Ignore remarks for now because backend doesn't support it yet
    const payload = {
      barcode: form.barcode,
      sku: form.sku,
      school: form.school,
      category: form.category,
      product_name: form.product_name,
      size: form.size,
      color: form.color,
      purchase_price: form.purchase_price,
      selling_price: form.selling_price,
      mrp: form.mrp,
      stock: form.stock,
    };

    try {
      if (editingProduct) {
        await updateProduct(editingProduct.id, payload);
        alert("Product Updated Successfully");
      } else {
        await addProduct(payload);
        alert("Product Added Successfully");
      }

      setForm(initialForm);
      setEditingProduct(null);
      loadProducts();
    } catch (err) {
      console.log(err);
      alert("Failed to Save Product");
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8">

      <h2 className="text-3xl font-bold text-slate-800 mb-8">
        {editingProduct ? "Edit Product" : "Add New Product"}
      </h2>

      <form
        onSubmit={handleSubmit}
        className="grid grid-cols-1 md:grid-cols-2 gap-5"
      >
        {/* School */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            School *
          </label>

          <select
            name="school"
            value={form.school}
            onChange={handleChange}
            className="w-full border rounded-xl p-3"
            required
          >
            <option value="">Select School</option>

            {schools.map((school) => (
              <option
                key={school.id}
                value={school.school_name}
              >
                {school.school_name}
              </option>
            ))}
          </select>
        </div>

        {/* Category */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            Category *
          </label>

          <select
            name="category"
            value={form.category}
            onChange={handleChange}
            className="w-full border rounded-xl p-3"
            required
          >
            <option value="">Select Category</option>

            {categories.map((cat) => (
              <option
                key={cat}
                value={cat}
              >
                {cat}
              </option>
            ))}
          </select>
        </div>

        {/* Product Name */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            Product Name *
          </label>

          <input
            name="product_name"
            value={form.product_name}
            onChange={handleChange}
            className="w-full border rounded-xl p-3"
            placeholder="School Shirt"
            required
          />
        </div>

        {/* Color */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            Color
          </label>

          <input
            name="color"
            value={form.color}
            onChange={handleChange}
            className="w-full border rounded-xl p-3"
            placeholder="White"
          />
        </div>

        {/* Barcode */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            Barcode
          </label>

          <input
            name="barcode"
            value={form.barcode}
            onChange={handleChange}
            className="w-full border rounded-xl p-3"
            placeholder="Barcode"
          />
        </div>

        {/* SKU */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            SKU
          </label>

          <input
            name="sku"
            value={form.sku}
            onChange={handleChange}
            className="w-full border rounded-xl p-3"
            placeholder="SKU"
          />
        </div>

        {/* Size */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            Size
          </label>

          <input
            name="size"
            value={form.size}
            onChange={handleChange}
            className="w-full border rounded-xl p-3"
            placeholder="M / 32"
          />
        </div>

        {/* Stock */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            Opening Stock
          </label>

          <input
            type="number"
            name="stock"
            value={form.stock}
            onChange={handleChange}
            className="w-full border rounded-xl p-3"
            required
          />
        </div>

        {/* Purchase Price */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            Purchase Price
          </label>

          <input
            type="number"
            name="purchase_price"
            value={form.purchase_price}
            onChange={handleChange}
            className="w-full border rounded-xl p-3"
          />
        </div>

        {/* Selling Price */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            Selling Price
          </label>

          <input
            type="number"
            name="selling_price"
            value={form.selling_price}
            onChange={handleChange}
            className="w-full border rounded-xl p-3"
            required
          />
        </div>

        {/* MRP */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            MRP
          </label>

          <input
            type="number"
            name="mrp"
            value={form.mrp}
            onChange={handleChange}
            className="w-full border rounded-xl p-3"
          />
        </div>

        {/* Remarks */}

        <div>
          <label className="block text-sm font-semibold mb-2">
            Remarks
          </label>

          <textarea
            rows="3"
            name="remarks"
            value={form.remarks}
            onChange={handleChange}
            className="w-full border rounded-xl p-3 resize-none"
            placeholder="Optional remarks..."
          />
        </div>

        {/* Save Button */}

        <div className="md:col-span-2 pt-4">
          <button
            type="submit"
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-xl transition duration-200 shadow-md hover:shadow-lg"
          >
            {editingProduct
              ? "Update Product"
              : "Save Product"}
          </button>
        </div>

      </form>

    </div>
  );
}