import axios from "axios";

const API = "http://localhost:5000/api/stock";

// =======================================
// CREATE STOCK ENTRY
// =======================================

export const createStockEntry = async (data) => {
  const response = await axios.post(API, data);
  return response.data;
};

// =======================================
// GET ALL STOCK ENTRIES
// =======================================

export const getStockEntries = async () => {
  const response = await axios.get(API);
  return response.data;
};

// =======================================
// GET SINGLE ENTRY
// =======================================

export const getStockEntry = async (id) => {
  const response = await axios.get(`${API}/${id}`);
  return response.data;
};