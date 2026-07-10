import { useRef } from "react";
import axios from "axios";
import { useReactToPrint } from "react-to-print";

import InvoicePrint from "./InvoicePrint";
import { useBilling } from "../../../context/BillingContext";

export default function ActionButtons() {
  const { state, dispatch } = useBilling();

  const printRef = useRef();

  const handlePrint = useReactToPrint({
    contentRef: printRef,
    documentTitle: state.invoiceNo || "Invoice",
  });

  const saveBill = async () => {
    if (state.items.length === 0) {
      alert("Please add at least one product.");
      return;
    }

    try {
      const response = await axios.post(
        "http://localhost:5000/api/invoices",
        {
          customer_name: state.customer?.name || "",
          customer_phone: state.customer?.phone || "",

          subtotal: state.subtotal,
          discount: state.billDiscount,
          gst: state.tax,
          round_off: state.roundOff,
          grand_total: state.grandTotal,

          paid_amount: state.paidAmount,
          balance: state.balance,
          payment_mode: state.paymentMode,

          items: state.items,
        }
      );

      dispatch({
        type: "SET_INVOICE_NO",
        payload: response.data.invoiceNo,
      });

      alert(
        `Invoice Saved Successfully!\nInvoice No: ${response.data.invoiceNo}`
      );

      // Print automatically after save
      setTimeout(() => {
        handlePrint();

        // Clear bill after printing
        setTimeout(() => {
          dispatch({
            type: "CLEAR_BILL",
          });
        }, 1000);
      }, 300);

    } catch (err) {
      console.error(err);
      alert("Failed to save bill.");
    }
  };

  return (
    <>
      {/* Hidden printable invoice */}
      <div
        style={{
          position: "absolute",
          left: "-9999px",
          top: 0,
        }}
      >
        <InvoicePrint ref={printRef} />
      </div>

      <div className="bg-white rounded-xl shadow-lg p-5">

        <h2 className="text-xl font-bold mb-4 text-indigo-700">
          Actions
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">

          {/* SAVE */}

          <button
            onClick={saveBill}
            disabled={state.items.length === 0}
            className={`py-3 rounded-lg font-semibold text-white transition ${
              state.items.length === 0
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            Save Bill
          </button>

          {/* PRINT */}

          <button
            onClick={() => {
              if (state.items.length === 0) {
                alert("Nothing to print.");
                return;
              }

              handlePrint();
            }}
            className="bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-semibold transition"
          >
            Print
          </button>

          {/* HOLD */}

          <button
            className="bg-yellow-500 hover:bg-yellow-600 text-white py-3 rounded-lg font-semibold transition"
          >
            Hold
          </button>

          {/* CLEAR */}

          <button
            onClick={() => {
              if (window.confirm("Clear current bill?")) {
                dispatch({
                  type: "CLEAR_BILL",
                });
              }
            }}
            className="bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg font-semibold transition"
          >
            Clear
          </button>

          {/* RETURN */}

          <button
            className="bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg font-semibold transition"
          >
            Return
          </button>

        </div>

      </div>
    </>
  );
}