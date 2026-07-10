import { forwardRef } from "react";
import { useBilling } from "../../../context/BillingContext";
import shop from "../../../config/shop";

const InvoicePrint = forwardRef((props, ref) => {
  const { state } = useBilling();

  return (
    <div
      ref={ref}
      style={{
        width: "80mm",
        padding: "8px",
        fontFamily: "monospace",
        background: "#fff",
        color: "#000",
        fontSize: "12px",
      }}
    >
      <div style={{ textAlign: "center" }}>
        <h2>{shop.name}</h2>

        <div>{shop.address}</div>

        <div>{shop.city}</div>

        <div>Phone : {shop.phone}</div>

        <div>GSTIN : {shop.gst}</div>

        <hr />

        <div>
          Invoice : {state.invoiceNo || "New Bill"}
        </div>

        <div>
          {new Date().toLocaleString()}
        </div>

        <hr />
      </div>

      <div>
        Customer :
        {" "}
        {state.customer?.name || "Walk In Customer"}
      </div>

      <div>
        Phone :
        {" "}
        Phone : {state.customer?.mobile || "-"}
      </div>

      <hr />

      <table width="100%">
        <thead>
          <tr>
            <th align="left">Item</th>
            <th>Qty</th>
            <th align="right">Amt</th>
          </tr>
        </thead>

        <tbody>

          {state.items.map((item) => (

            <tr key={`${item.id}-${item.size}-${item.color}`}>
              <td>{item.product_name}</td>

              <td align="center">
                {item.qty}
              </td>

              <td align="right">
                ₹{(item.qty * item.price).toFixed(2)}
              </td>
            </tr>

          ))}

        </tbody>
      </table>

      <hr />

      <table width="100%">
        <tbody>

          <tr>
            <td>Subtotal</td>
            <td align="right">
              ₹{Number(state.subtotal || 0).toFixed(2)}
            </td>
          </tr>

          <tr>
            <td>Discount</td>
            <td align="right">
              ₹{Number(state.billDiscount || 0).toFixed(2)}
            </td>
          </tr>

          <tr>
            <td>Round Off</td>
            <td align="right">
              ₹{Number(state.roundOff || 0).toFixed(2)}
            </td>
          </tr>

          <tr>
            <td>
              <strong>Grand Total</strong>
            </td>

            <td align="right">
              <strong>
                ₹{Number(state.grandTotal || 0).toFixed(2)}
              </strong>
            </td>
          </tr>

          <tr>
            <td>Paid</td>
            <td align="right">
              ₹{Number(state.paidAmount || 0).toFixed(2)}
            </td>
          </tr>

          <tr>
            <td>Balance</td>
            <td align="right">
              ₹{Number(state.balance || 0).toFixed(2)}
            </td>
          </tr>

        </tbody>
      </table>

      <hr />

      <div style={{ textAlign: "center" }}>

        Payment :
        {" "}
        {state.paymentMode}

        <br />

        <br />

        Thank You!

        <br />

        Visit Again 🙏

      </div>

    </div>
  );
});

export default InvoicePrint;