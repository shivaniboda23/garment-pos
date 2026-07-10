const express = require("express");
const router = express.Router();

const {
  getSchools,
} = require("../controllers/schoolController");

router.get("/", getSchools);

module.exports = router;