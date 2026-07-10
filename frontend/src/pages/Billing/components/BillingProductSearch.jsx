import { useEffect, useState } from "react";
import { Search, Package } from "lucide-react";

import { useBilling } from "../../../context/BillingContext";

import { getSchools } from "../../../services/schoolService";
import { getCategories } from "../../../services/categoryService";
import { getProducts } from "../../../services/productService";

export default function BillingProductSearch() {
  const { dispatch } = useBilling();

  const [schools, setSchools] = useState([]);
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);

  const [selectedSchool, setSelectedSchool] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadSchools();
    loadCategories();
  }, []);

  useEffect(() => {
    loadProducts();
  }, [selectedSchool, selectedCategory]);

  const loadSchools = async () => {
    try {
      const data = await getSchools();
      setSchools(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await getCategories();
      setCategories(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadProducts = async () => {
    try {
      const data = await getProducts(
        selectedSchool,
        selectedCategory
      );

      setProducts(data);
    } catch (err) {
      console.error(err);
    }
  };

  const filteredProducts = products.filter((product) => {
    if (!search.trim()) return true;

    return (
      product.product_name
        ?.toLowerCase()
        .includes(search.toLowerCase()) ||
      product.barcode
        ?.toLowerCase()
        .includes(search.toLowerCase()) ||
      product.sku
        ?.toLowerCase()
        .includes(search.toLowerCase())
    );
  });

  const addProduct = (product) => {
    dispatch({
      type: "ADD_ITEM",
      payload: {
        id: product.id,
        barcode: product.barcode,
        sku: product.sku,
        product_name: product.product_name,
        school: product.school,
        category: product.category,
        size: product.size,
        color: product.color,
        qty: 1,
        price: Number(product.selling_price),
        gst: Number(product.gst || 0),
        discount: 0,
      },
    });

    setSearch("");
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">

      <div className="flex items-center gap-3 mb-6">

        <Package className="text-blue-600" size={28} />

        <h2 className="text-2xl font-bold text-blue-700">
          Product Search
        </h2>

      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">

        <select
          value={selectedSchool}
          onChange={(e) => {
            setSelectedSchool(e.target.value);

            dispatch({
              type: "SET_SCHOOL",
              payload: e.target.value,
            });
          }}
          className="border rounded-xl p-3 focus:ring-2 focus:ring-blue-500 outline-none"
        >
          <option value="">All Schools</option>

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
          value={selectedCategory}
          onChange={(e) =>
            setSelectedCategory(e.target.value)
          }
          className="border rounded-xl p-3 focus:ring-2 focus:ring-blue-500 outline-none"
        >
          <option value="">All Categories</option>

          {categories.map((category) => (
            <option
              key={category.id}
              value={category.name}
            >
              {category.name}
            </option>
          ))}
        </select>

      </div>

      <div className="relative mb-5">

        <Search
          className="absolute left-3 top-3.5 text-gray-400"
          size={20}
        />

        <input
          value={search}
          onChange={(e) =>
            setSearch(e.target.value)
          }
          placeholder="Search by Product Name, Barcode or SKU..."
          className="w-full border rounded-xl py-3 pl-10 pr-4 focus:ring-2 focus:ring-blue-500 outline-none"
        />

      </div>

      <div className="border rounded-xl max-h-96 overflow-y-auto">

        {filteredProducts.length === 0 ? (

          <div className="text-center p-10 text-gray-500">
            No Products Found
          </div>

        ) : (

          filteredProducts.map((product) => (

            <div
              key={product.id}
              onClick={() => addProduct(product)}
              className="flex justify-between items-center p-4 border-b hover:bg-blue-50 cursor-pointer transition"
            >

              <div>

                <div className="font-bold text-gray-800">
                  {product.product_name}
                </div>

                <div className="text-sm text-gray-500">
                  {product.school}
                </div>

                <div className="text-sm text-gray-500">
                  {product.category}
                </div>

                <div className="text-xs text-gray-400 mt-1">
                  SKU : {product.sku}
                </div>

              </div>

              <div className="text-right">

                <div className="font-bold text-lg text-green-700">
                  ₹ {Number(product.selling_price).toFixed(2)}
                </div>

                <div className="text-sm">
                  Size : {product.size}
                </div>

                <div
                  className={`mt-2 inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                    product.stock > 10
                      ? "bg-green-100 text-green-700"
                      : "bg-red-100 text-red-700"
                  }`}
                >
                  Stock : {product.stock}
                </div>

              </div>

            </div>

          ))

        )}

      </div>

    </div>
  );
}