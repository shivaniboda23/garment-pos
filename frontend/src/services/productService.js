import axios from "axios";

const API = "http://localhost:5000/api/products";

// ======================================================
// GET PRODUCTS
// ======================================================

export const getProducts = async (
  school = "",
  category = "",
  search = ""
) => {

  let url = API;

  const params = [];

  if (school) {
    params.push(
      `school=${encodeURIComponent(school)}`
    );
  }

  if (category) {
    params.push(
      `category=${encodeURIComponent(category)}`
    );
  }

  if (search) {
    params.push(
      `search=${encodeURIComponent(search)}`
    );
  }

  if (params.length) {
    url += "?" + params.join("&");
  }

  const res = await axios.get(url);

  return res.data;

};

// ======================================================
// GET ALL SIZE VARIANTS
// ======================================================

export const getProductVariants = async (
  productName,
  school,
  category
) => {

  const res = await axios.get(
    `${API}/variants`,
    {
      params: {
        product_name: productName,
        school,
        category,
      },
    }
  );

  return res.data;

};

// ======================================================
// ADD PRODUCT
// ======================================================

export const addProduct = async (data) => {

  const res = await axios.post(
    API,
    data
  );

  return res.data;

};

// ======================================================
// UPDATE PRODUCT
// ======================================================

export const updateProduct = async (
  id,
  data
) => {

  const res = await axios.put(
    `${API}/${id}`,
    data
  );

  return res.data;

};

// ======================================================
// DELETE PRODUCT
// ======================================================

export const deleteProduct = async (id) => {

  const res = await axios.delete(
    `${API}/${id}`
  );

  return res.data;

};