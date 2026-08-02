import { useEffect, useState } from "react";

import { getSchools } from "../../../services/schoolService";
import { getCategories } from "../../../services/categoryService";
import { bulkAddProducts } from "../../../services/productService";

const shirtSizes = [
  "S",
  "M",
  "L",
  "XL",
  "XXL",
  "XXXL",
];

const pantSizes = [
  "22",
  "24",
  "26",
  "28",
  "30",
  "32",
  "34",
  "36",
  "38",
  "40",
  "42",
  "44",
  "46",
  "48",
];

export default function BulkProductForm() {

  const [schools, setSchools] = useState([]);
  const [categories, setCategories] = useState([]);

  const [selectedSizes, setSelectedSizes] = useState([]);

  const [form, setForm] = useState({

    school: "",

    category: "",

    product_name: "",

    color: "",

    sku: "",

    barcode: "",

    purchase_price: "",

    selling_price: "",

    mrp: "",

    stock: 0,

    remarks: "",

  });

  useEffect(() => {

    loadData();

  }, []);

  const loadData = async () => {

    try {

      const schoolsData = await getSchools();

      const categoryData = await getCategories();

      setSchools(schoolsData);

      setCategories(categoryData);

    } catch (err) {

      console.error(err);

    }

  };

  const currentSizes =
    form.category === "Uniform"
      ? pantSizes
      : shirtSizes;

  const toggleSize = (size) => {

    if (selectedSizes.includes(size)) {

      setSelectedSizes(
        selectedSizes.filter((s) => s !== size)
      );

    } else {

      setSelectedSizes([
        ...selectedSizes,
        size,
      ]);

    }

  };

  const handleChange = (e) => {

    setForm({

      ...form,

      [e.target.name]: e.target.value,

    });

  };

  const handleSubmit = async () => {

    if (selectedSizes.length === 0) {

      alert("Select at least one size");

      return;

    }

    try {

      await bulkAddProducts({

        ...form,

        sizes: selectedSizes,

      });

      alert("Products Created Successfully");

      setSelectedSizes([]);

      setForm({

        school: "",

        category: "",

        product_name: "",

        color: "",

        sku: "",

        barcode: "",

        purchase_price: "",

        selling_price: "",

        mrp: "",

        stock: 0,

        remarks: "",

      });

    } catch (err) {

      console.error(err);

      alert("Failed to create products");

    }

  };

  return (

    <div className="bg-white rounded-xl shadow-lg p-6">

      <div className="grid md:grid-cols-2 gap-4">

        <select
          name="school"
          value={form.school}
          onChange={handleChange}
          className="border rounded-lg p-3"
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

        <select
          name="category"
          value={form.category}
          onChange={handleChange}
          className="border rounded-lg p-3"
        >
          <option value="">
            Select Category
          </option>

          {categories.map((cat) => (

            <option
              key={cat.id}
              value={cat.name}
            >
              {cat.name}
            </option>

          ))}

        </select>

        <input
          name="product_name"
          placeholder="Product Name"
          value={form.product_name}
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
          name="sku"
          placeholder="Base SKU"
          value={form.sku}
          onChange={handleChange}
          className="border rounded-lg p-3"
        />

        <input
          name="barcode"
          placeholder="Base Barcode"
          value={form.barcode}
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
          placeholder="Initial Stock"
          value={form.stock}
          onChange={handleChange}
          className="border rounded-lg p-3"
        />

      </div>

      <textarea
        name="remarks"
        placeholder="Remarks"
        value={form.remarks}
        onChange={handleChange}
        className="border rounded-lg p-3 w-full mt-4"
      />

      <div className="mt-6">

        <h3 className="font-bold mb-3">
          Select Sizes
        </h3>

        <div className="grid grid-cols-5 gap-3">

          {currentSizes.map((size) => (

            <button
              key={size}
              type="button"
              onClick={() => toggleSize(size)}
              className={`rounded-lg p-2 border font-semibold ${
                selectedSizes.includes(size)
                  ? "bg-blue-600 text-white"
                  : "bg-white"
              }`}
            >
              {size}
            </button>

          ))}

        </div>

      </div>

      <button
        onClick={handleSubmit}
        className="mt-8 bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold"
      >
        Create Products
      </button>

    </div>

  );

}