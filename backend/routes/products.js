const express = require("express");

const router = express.Router();

const {
  getProducts,
  getProductVariants,
  addProduct,
  updateProduct,
  deleteProduct,
} = require("../controllers/productController");

// ======================================================
// GET PRODUCTS
// ======================================================

router.get("/", getProducts);

// ======================================================
// GET ALL SIZE VARIANTS OF A PRODUCT
// Example:
// /api/products/variants?product_name=School Shirt&school=Sri Chaitanya&category=Uniform
// ======================================================

router.get("/variants", getProductVariants);

// ======================================================
// ADD PRODUCT
// ======================================================

router.post("/", addProduct);

// ======================================================
// UPDATE PRODUCT
// ======================================================

router.put("/:id", updateProduct);

// ======================================================
// DELETE PRODUCT
// ======================================================

router.delete("/:id", deleteProduct);

module.exports = router;