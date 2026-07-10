import axios from "axios";

const API = "http://localhost:5000/api/products";

export const getProducts = async (school = "", category = "") => {
  let url = API;

  const params = [];

  if (school) {
    params.push(`school=${encodeURIComponent(school)}`);
  }

  if (category) {
    params.push(`category=${encodeURIComponent(category)}`);
  }

  if (params.length > 0) {
    url += "?" + params.join("&");
  }

  console.log("Fetching:", url);

  const res = await axios.get(url);

  console.log(res.data);

  return res.data;
};

export const addProduct = async (data) => {
  const res = await axios.post(API, data);
  return res.data;
};

export const updateProduct = async (id, data) => {
  const res = await axios.put(`${API}/${id}`, data);
  return res.data;
};

export const deleteProduct = async (id) => {
  const res = await axios.delete(`${API}/${id}`);
  return res.data;
};