import { useEffect, useState } from "react";
import axios from "axios";
import {
  addProduct,
  updateProduct,
} from "../../../services/productService";

export default function ProductForm({
  loadProducts,
  editingProduct,
  setEditingProduct,
}) {

  const [schools, setSchools] = useState([]);

  const [form, setForm] = useState({
    barcode: "",
    sku: "",
    school: "",
    category: "",
    product_name: "",
    size: "",
    color: "",
    purchase_price: "",
    selling_price: "",
    mrp: "",
    stock: "",
  });

  useEffect(() => {
    loadSchools();
  }, []);

  useEffect(() => {

    if (editingProduct) {
      setForm(editingProduct);
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

    try {

      if (editingProduct) {

        await updateProduct(editingProduct.id, form);

        alert("Product Updated");

      } else {

        await addProduct(form);

        alert("Product Added");

      }

      setForm({
        barcode: "",
        sku: "",
        school: "",
        category: "",
        product_name: "",
        size: "",
        color: "",
        purchase_price: "",
        selling_price: "",
        mrp: "",
        stock: "",
      });

      setEditingProduct(null);

      loadProducts();

    } catch (err) {

      console.log(err);

      alert("Failed");

    }

  };

  return (

    <div className="bg-white rounded-xl shadow-lg p-6">

      <h2 className="text-2xl font-bold mb-6">

        {editingProduct
          ? "Edit Product"
          : "Add Product"}

      </h2>

      <form
        onSubmit={handleSubmit}
        className="grid md:grid-cols-2 gap-4"
      >

        <select
          name="school"
          value={form.school}
          onChange={handleChange}
          className="border rounded-lg p-3"
          required
        >

          <option value="">
            Select School
          </option>

          {schools.map((school) => (

            <option
              key={school.id}
              value={school.school_name}
            >
              {school.school_name}
            </option>

          ))}

        </select>

        <input
          name="category"
          placeholder="Category"
          value={form.category}
          onChange={handleChange}
          className="border rounded-lg p-3"
          required
        />

        <input
          name="product_name"
          placeholder="Product Name"
          value={form.product_name}
          onChange={handleChange}
          className="border rounded-lg p-3"
          required
        />

        <input
          name="barcode"
          placeholder="Barcode"
          value={form.barcode}
          onChange={handleChange}
          className="border rounded-lg p-3"
        />

        <input
          name="sku"
          placeholder="SKU"
          value={form.sku}
          onChange={handleChange}
          className="border rounded-lg p-3"
        />

        <input
          name="size"
          placeholder="Size"
          value={form.size}
          onChange={handleChange}
          className="border rounded-lg p-3"
        />

        <input
          name="color"
          placeholder="Color"
          value={form.color}
          onChange={handleChange}
          className="border rounded-lg p-3"
        />

        <input
          type="number"
          name="purchase_price"
          placeholder="Purchase Price"
          value={form.purchase_price}
          onChange={handleChange}
          className="border rounded-lg p-3"
        />

        <input
          type="number"
          name="selling_price"
          placeholder="Selling Price"
          value={form.selling_price}
          onChange={handleChange}
          className="border rounded-lg p-3"
          required
        />

        <input
          type="number"
          name="mrp"
          placeholder="MRP"
          value={form.mrp}
          onChange={handleChange}
          className="border rounded-lg p-3"
        />

        <input
          type="number"
          name="stock"
          placeholder="Opening Stock"
          value={form.stock}
          onChange={handleChange}
          className="border rounded-lg p-3"
          required
        />

        <button
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg p-3 col-span-2"
        >

          {editingProduct
            ? "Update Product"
            : "Save Product"}

        </button>

      </form>

    </div>

  );

}