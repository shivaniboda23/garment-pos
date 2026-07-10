const pool = require("../config/db");

exports.saveInvoice = async (req, res) => {
  const client = await pool.connect();

  try {
    await client.query("BEGIN");

    const {
      customer_name,
      customer_phone,
      subtotal,
      discount,
      gst,
      round_off,
      grand_total,
      paid_amount,
      balance,
      payment_mode,
      items,
    } = req.body;

    const invoiceNo = "BG-" + Date.now();

    const invoiceResult = await client.query(
      `INSERT INTO invoices
      (
        invoice_no,
        customer_name,
        customer_phone,
        subtotal,
        discount,
        gst,
        round_off,
        grand_total,
        paid_amount,
        balance,
        payment_mode
      )
      VALUES
      ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
      RETURNING id`,
      [
        invoiceNo,
        customer_name,
        customer_phone,
        subtotal,
        discount,
        gst,
        round_off,
        grand_total,
        paid_amount,
        balance,
        payment_mode,
      ]
    );

    const invoiceId = invoiceResult.rows[0].id;

    for (const item of items) {
      await client.query(
        `INSERT INTO invoice_items
        (
          invoice_id,
          product_id,
          quantity,
          price,
          discount,
          gst,
          total
        )
        VALUES($1,$2,$3,$4,$5,$6,$7)`,
        [
          invoiceId,
          item.id,
          item.qty,
          item.price,
          item.discount,
          item.gst,
          item.qty * item.price,
        ]
      );

      await client.query(
        `UPDATE products
         SET stock = stock - $1
         WHERE id = $2`,
        [item.qty, item.id]
      );
    }

    await client.query("COMMIT");

    res.json({
      success: true,
      invoiceNo,
    });
  } catch (err) {
    await client.query("ROLLBACK");
    console.error(err);
    res.status(500).json(err);
  } finally {
    client.release();
  }
};