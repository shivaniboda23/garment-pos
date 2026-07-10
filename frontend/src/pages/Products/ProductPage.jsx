import { useEffect, useState } from "react";

import ProductForm from "./components/ProductForm";
import ProductSearch from "./components/ProductSearch";
import ProductTable from "./components/ProductTable";

import { getProducts } from "../../services/productService";

export default function ProductPage() {

  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [editingProduct, setEditingProduct] = useState(null);

  const loadProducts = async () => {
    try {

      const data = await getProducts();

      setProducts(data);
      setFilteredProducts(data);

    } catch (err) {

      console.error(err);

    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  return (

    <div className="p-6">

      <ProductForm
        loadProducts={loadProducts}
        editingProduct={editingProduct}
        setEditingProduct={setEditingProduct}
      />

      <ProductSearch
        products={products}
        setFilteredProducts={setFilteredProducts}
      />

      <ProductTable
        products={filteredProducts}
        loadProducts={loadProducts}
        setEditingProduct={setEditingProduct}
      />

    </div>

  );

}