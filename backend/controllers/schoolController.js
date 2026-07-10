const pool = require("../config/db");

// Get all schools
exports.getSchools = async (req, res) => {
  try {
    const result = await pool.query(
      "SELECT * FROM schools ORDER BY school_name"
    );

    res.json(result.rows);
  } catch (err) {
    console.error(err);

    res.status(500).json({
      message: "Failed to fetch schools",
    });
  }
};