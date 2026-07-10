const express = require("express");
const router = express.Router();

const {
  saveInvoice,
} = require("../controllers/invoiceController");

router.post("/", saveInvoice);

module.exports = router;