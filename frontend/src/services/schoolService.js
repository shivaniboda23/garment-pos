import axios from "axios";

const API = "http://localhost:5000/api/schools";

export const getSchools = async () => {
  const res = await axios.get(API);
  return res.data;
};