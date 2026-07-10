import { useState } from "react";

export default function ProductSearch({
  products,
  setFilteredProducts,
}) {
  const [search, setSearch] = useState("");

  const handleSearch = (value) => {
    setSearch(value);

    const keyword = value.toLowerCase();

    const filtered = products.filter((product) => {
      return (
        product.product_name?.toLowerCase().includes(keyword) ||
        product.school?.toLowerCase().includes(keyword) ||
        product.category?.toLowerCase().includes(keyword) ||
        product.barcode?.toLowerCase().includes(keyword) ||
        product.sku?.toLowerCase().includes(keyword)
      );
    });

    setFilteredProducts(filtered);
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-5 mb-5">

      <h2 className="text-xl font-bold text-blue-700 mb-4">
        Search Products
      </h2>

      <input
        type="text"
        placeholder="Search School / Category / Product / Barcode / SKU..."
        value={search}
        onChange={(e) => handleSearch(e.target.value)}
        className="w-full border rounded-lg p-3 focus:ring-2 focus:ring-blue-500 outline-none"
      />

    </div>
  );
}