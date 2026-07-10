const express = require("express");
const cors = require("cors");
require("dotenv").config();

const pool = require("./config/db");

// Routes
const productRoutes = require("./routes/products");
const invoiceRoutes = require("./routes/invoices");
const schoolRoutes = require("./routes/schoolRoutes");
const categoryRoutes = require("./routes/categories");
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// ----------------------
// Test Route
// ----------------------
app.get("/", (req, res) => {
  res.json({
    message: "Bhavani Garments ERP Backend Running 🚀",
  });
});

// ----------------------
// Database Test
// ----------------------
app.get("/test-db", async (req, res) => {
  try {
    const result = await pool.query("SELECT NOW()");
    res.json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json(err);
  }
});

// ----------------------
// API Routes
// ----------------------
app.use("/api/products", productRoutes);

app.use("/api/invoices", invoiceRoutes);

app.use("/api/schools", schoolRoutes);

app.use("/api/categories", categoryRoutes);

// ----------------------
// Server
// ----------------------
const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`✅ Server running on http://localhost:${PORT}`);
});