import axios from "axios";

const API = "http://localhost:5000/api/categories";

export const getCategories = async () => {
  const res = await axios.get(API);
  return res.data;
};