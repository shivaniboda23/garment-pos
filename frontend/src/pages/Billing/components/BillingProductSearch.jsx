import { useEffect, useState } from "react";
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
        .toLowerCase()
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
        discount: 0,
        status: "Delivered",
      },
    });

    setSearch("");
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-5">

      <h2 className="text-xl font-bold text-blue-700 mb-5">
        Add Products
      </h2>

      <div className="grid md:grid-cols-2 gap-4 mb-4">

        <select
          value={selectedSchool}
          onChange={(e) => {
            const school = e.target.value;

            setSelectedSchool(school);

            dispatch({
              type: "SET_SCHOOL",
              payload: school,
            });
          }}
          className="border rounded-lg p-3"
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
          className="border rounded-lg p-3"
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

      <input
        className="w-full border rounded-lg p-3"
        placeholder="Search Product / Barcode / SKU..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="mt-4 max-h-96 overflow-y-auto border rounded-lg">

        {filteredProducts.length === 0 ? (
          <div className="p-5 text-center text-gray-500">
            No Products Found
          </div>
        ) : (
          filteredProducts.map((product) => (
            <div
              key={product.id}
              onClick={() => addProduct(product)}
              className="p-4 border-b hover:bg-blue-50 cursor-pointer"
            >
              <div className="font-semibold">
                {product.product_name}
              </div>

              <div className="text-sm text-gray-500">
                {product.school}
              </div>

              <div className="text-sm text-gray-500">
                {product.category}
              </div>

              <div className="flex justify-between mt-2">
                <span>
                  Size : {product.size}
                </span>

                <span className="font-semibold text-green-700">
                  ₹ {Number(product.selling_price).toFixed(2)}
                </span>
              </div>
            </div>
          ))
        )}

      </div>
    </div>
  );
}