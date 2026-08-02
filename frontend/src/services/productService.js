import axios from "axios";

const API = "http://localhost:5000/api/products";

// ===============================
// GET PRODUCTS
// ===============================
export const getProducts = async (
  school = "",
  category = "",
  search = ""
) => {
  const params = {};

  if (school) params.school = school;
  if (category) params.category = category;
  if (search) params.search = search;

  const res = await axios.get(API, { params });

  return res.data;
};

// ===============================
// GET PRODUCT VARIANTS (ALL SIZES)
// ===============================
export const getProductVariants = async (
  productName,
  school,
  category
) => {
  const res = await axios.get(`${API}/variants`, {
    params: {
      product_name: productName,
      school,
      category,
    },
  });

  return res.data;
};

// ===============================
// ADD PRODUCT
// ===============================
export const addProduct = async (product) => {
  const res = await axios.post(API, product);
  return res.data;
};

// ===============================
// UPDATE PRODUCT
// ===============================
export const updateProduct = async (id, product) => {
  const res = await axios.put(`${API}/${id}`, product);
  return res.data;
};

// ===============================
// DELETE PRODUCT
// ===============================
export const deleteProduct = async (id) => {
  const res = await axios.delete(`${API}/${id}`);
  return res.data;
};
export async function bulkAddProducts(data) {

  const response = await fetch(
    "http://localhost:5000/api/products/bulk",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  if (!response.ok) {
    throw new Error("Failed to create products");
  }

  return response.json();

}