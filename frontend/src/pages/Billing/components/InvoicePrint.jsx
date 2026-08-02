import { forwardRef } from "react";
import { useBilling } from "../../../context/BillingContext";
import shop from "../../../config/shop";

const InvoicePrint = forwardRef((props, ref) => {
  const { state } = useBilling();

  const pendingItems = state.items.filter(
    (item) => item.status === "Pending"
  );

  const totalItems = state.items.reduce(
    (sum, item) => sum + Number(item.qty),
    0
  );

  const today = new Date();

  const date = today.toLocaleDateString("en-GB");

  const time = today.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      ref={ref}
      style={{
        width: "80mm",
        background: "#fff",
        color: "#000",
        padding: "8px",
        fontFamily: "monospace",
        fontSize: "11px",
        lineHeight: "1.45",
      }}
    >

      {/* ================= HEADER ================= */}

      <div style={{ textAlign: "center" }}>

        <div
          style={{
            width: 55,
            height: 55,
            borderRadius: "50%",
            background: "#111",
            color: "#fff",
            margin: "0 auto 8px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            fontWeight: "bold",
            fontSize: 24,
          }}
        >
          BG
        </div>

        <div
          style={{
            fontSize: 18,
            fontWeight: "bold",
          }}
        >
          BHAVANI GARMENTS
        </div>

        <div>
          School & College Uniforms
        </div>

        <div style={{ marginTop: 6 }}>
          {shop.address}
        </div>

        <div>
          Phone : {shop.phone}
        </div>

        <hr />

      </div>

      {/* ================= BILL INFO ================= */}

      <table width="100%">

        <tbody>

          <tr>

            <td>Bill No</td>

            <td align="right">
              {state.invoiceNo || "NEW"}
            </td>

          </tr>

          <tr>

            <td>Date</td>

            <td align="right">
              {date}
            </td>

          </tr>

          <tr>

            <td>Time</td>

            <td align="right">
              {time}
            </td>

          </tr>

        </tbody>

      </table>

      <hr />

      {/* ================= CUSTOMER ================= */}

      <table width="100%">

        <tbody>

          <tr>

            <td>Name</td>

            <td align="right">
              {state.customer.name || "Walk In"}
            </td>

          </tr>

          <tr>

            <td>Phone</td>

            <td align="right">
              {state.customer.mobile || "-"}
            </td>

          </tr>

          <tr>

            <td>School</td>

            <td align="right">
              {state.customer.school || "-"}
            </td>

          </tr>

        </tbody>

      </table>

      <hr />

      {/* ================= ITEMS ================= */}

      <table width="100%">

        <thead>

          <tr>

            <th align="left">
              Code
            </th>

            <th align="left">
              Item
            </th>

            <th>
              Qty
            </th>

            <th align="right">
              Price
            </th>

            <th align="right">
              Amount
            </th>

            <th align="center">
              Status
            </th>

          </tr>

        </thead>

        <tbody>
          {state.items.map((item) => {

  const amount = item.qty * item.price;

  return (

    <tr key={item.id}>

      <td>
        {item.sku}
      </td>

      <td>
        {item.product_name}
        <br />

        <span style={{ fontSize: 10 }}>
          {item.size}
        </span>
      </td>

      <td align="center">
        {item.qty}
      </td>

      <td align="right">
        ₹{Number(item.price).toFixed(0)}
      </td>

      <td align="right">
        ₹{Number(amount).toFixed(0)}
      </td>

      <td align="center">
        {item.status}
      </td>

    </tr>

  );

})}

</tbody>

</table>

<hr />

{/* ================= TOTALS ================= */}

<table width="100%">

  <tbody>

    <tr>

      <td>
        Items
      </td>

      <td align="right">
        {totalItems}
      </td>

    </tr>

    <tr>

      <td>
        Subtotal
      </td>

      <td align="right">
        ₹{Number(state.subtotal).toFixed(2)}
      </td>

    </tr>

    <tr>

      <td>
        Discount
      </td>

      <td align="right">
        ₹{Number(state.billDiscount).toFixed(2)}
      </td>

    </tr>

    <tr>

      <td
        style={{
          fontWeight: "bold",
          fontSize: 14,
        }}
      >
        Grand Total
      </td>

      <td
        align="right"
        style={{
          fontWeight: "bold",
          fontSize: 14,
        }}
      >
        ₹{Number(state.grandTotal).toFixed(2)}
      </td>

    </tr>

    <tr>

      <td>
        Paid
      </td>

      <td align="right">
        ₹{Number(state.paidAmount).toFixed(2)}
      </td>

    </tr>

    <tr>

      <td>
        Due
      </td>

      <td align="right">
        ₹{Number(state.balance).toFixed(2)}
      </td>

    </tr>

    <tr>

      <td>
        Payment
      </td>

      <td align="right">
        {state.paymentMode}
      </td>

    </tr>

  </tbody>

</table>

{/* ================= PENDING ITEMS ================= */}

{pendingItems.length > 0 && (

  <>

    <hr />

    <div
      style={{
        fontWeight: "bold",
        marginBottom: 6,
      }}
    >
      Pending Items
    </div>

    <table width="100%">

      <thead>

        <tr>

          <th align="left">
            Item
          </th>

          <th align="center">
            Size
          </th>

          <th align="center">
            Qty
          </th>

        </tr>

      </thead>

      <tbody>

        {pendingItems.map((item) => (

          <tr key={item.id}>

            <td>{item.product_name}</td>

            <td align="center">
              {item.size}
            </td>

            <td align="center">
              {item.qty}
            </td>

          </tr>

        ))}

      </tbody>

    </table>

  </>

)}
      {/* ================= FOOTER ================= */}

      <hr />

      <div
        style={{
          textAlign: "center",
          marginTop: 8,
        }}
      >
        <div
          style={{
            fontWeight: "bold",
            fontSize: 14,
          }}
        >
          Thank You for Shopping!
        </div>

        <div
          style={{
            marginTop: 3,
          }}
        >
          Bhavani Garments
        </div>

        <div
          style={{
            marginTop: 10,
            fontSize: 10,
          }}
        >
          Exchange within 7 days with bill.
        </div>

        <div
          style={{
            fontSize: 10,
          }}
        >
          NO RETURN ONLY SIZE EXCHANGE IS AVAILABLE.
        </div>

        <div
          style={{
            marginTop: 10,
            fontSize: 10,
          }}
        >
          ****************************************
        </div>

      </div>

    </div>

  );

});

InvoicePrint.displayName = "InvoicePrint";

export default InvoicePrint;