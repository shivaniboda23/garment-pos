const pool = require("../config/db");

// ==========================================
// GET PRODUCTS
// Supports:
// /api/products
// /api/products?school=Sri Chaitanya
// /api/products?school=Sri Chaitanya&category=Uniform
// ==========================================
exports.getProducts = async (req, res) => {
  try {
    console.log("==================================");
    console.log("Incoming Query:", req.query);

    const { school, category, search } = req.query;

    let query = `
      SELECT
        id,
        barcode,
        sku,
        product_name,
        school,
        category,
        size,
        color,
        purchase_price,
        selling_price,
        mrp,
        stock,
        remarks,
        created_at
      FROM products
      WHERE 1=1
    `;

    const values = [];

    if (school) {
      values.push(school);
      query += ` AND school = $${values.length}`;
    }

    if (category) {
      values.push(category);
      query += ` AND category = $${values.length}`;
    }

    if (search) {
      values.push(`%${search}%`);
      query += `
        AND (
          LOWER(product_name) LIKE LOWER($${values.length})
          OR LOWER(barcode) LIKE LOWER($${values.length})
          OR LOWER(sku) LIKE LOWER($${values.length})
        )
      `;
    }

    query += `
      ORDER BY school, category, product_name, size
    `;

    console.log("SQL:");
    console.log(query);

    console.log("VALUES:");
    console.log(values);

    const result = await pool.query(query, values);

    console.log("ROWS:");
    console.log(result.rows);

    res.json(result.rows);

  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Failed to fetch products" });
  }
};

// ==========================================
// ADD PRODUCT
// ==========================================
exports.addProduct = async (req, res) => {
  try {

    const {
      barcode,
      sku,
      school,
      category,
      product_name,
      size,
      color,
      purchase_price,
      selling_price,
      mrp,
      stock,
      remarks,
    } = req.body;

    const result = await pool.query(
      `
      INSERT INTO products
      (
        barcode,
        sku,
        school,
        category,
        product_name,
        size,
        color,
        purchase_price,
        selling_price,
        mrp,
        stock,
        remarks
      )
      VALUES
      ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
      RETURNING *
      `,
      [
        barcode,
        sku,
        school,
        category,
        product_name,
        size,
        color,
        purchase_price,
        selling_price,
        mrp,
        stock,
        remarks,
      ]
    );

    res.status(201).json(result.rows[0]);

  } catch (err) {

    console.error(err);

    res.status(500).json({
      message: "Failed to add product",
    });

  }
};

// ==========================================
// UPDATE PRODUCT
// ==========================================
exports.updateProduct = async (req, res) => {
  try {

    const { id } = req.params;

    const {
      barcode,
      sku,
      school,
      category,
      product_name,
      size,
      color,
      purchase_price,
      selling_price,
      mrp,
      stock,
      remarks,
    } = req.body;

    const result = await pool.query(
      `
      UPDATE products
      SET
        barcode=$1,
        sku=$2,
        school=$3,
        category=$4,
        product_name=$5,
        size=$6,
        color=$7,
        purchase_price=$8,
        selling_price=$9,
        mrp=$10,
        stock=$11,
        remarks=$12
      WHERE id=$13
      RETURNING *
      `,
      [
        barcode,
        sku,
        school,
        category,
        product_name,
        size,
        color,
        purchase_price,
        selling_price,
        mrp,
        stock,
        remarks,
        id,
      ]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        message: "Product not found",
      });
    }

    res.json(result.rows[0]);

  } catch (err) {

    console.error(err);

    res.status(500).json({
      message: "Failed to update product",
    });

  }
};

// ==========================================
// DELETE PRODUCT
// ==========================================
exports.deleteProduct = async (req, res) => {
  try {

    const { id } = req.params;

    const result = await pool.query(
      "DELETE FROM products WHERE id=$1 RETURNING *",
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        message: "Product not found",
      });
    }

    res.json({
      success: true,
      message: "Product deleted successfully",
    });

  } catch (err) {

    console.error(err);

    res.status(500).json({
      message: "Failed to delete product",
    });

  }
};