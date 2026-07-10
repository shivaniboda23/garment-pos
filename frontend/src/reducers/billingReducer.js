export const initialState = {
  invoiceNo: "",

  customer: {
    name: "",
    mobile: "",
    school: "",
    remarks: "",
  },

  selectedSchool: "",

  items: [],

  subtotal: 0,
  billDiscount: 0,
  roundOff: 0,
  grandTotal: 0,

  paidAmount: 0,
  balance: 0,

  paymentMode: "Cash",

  status: "Draft",
};

function calculateTotals(items, billDiscount = 0) {
  let subtotal = 0;

  items.forEach((item) => {
    const qty = Number(item.qty || 0);
    const price = Number(item.price || 0);
    const discount = Number(item.discount || 0);

    subtotal += qty * price - (qty * price * discount) / 100;
  });

  const totalAfterDiscount =
    subtotal - Number(billDiscount || 0);

  const grandTotal = Math.round(totalAfterDiscount);

  const roundOff = Number(
    (grandTotal - totalAfterDiscount).toFixed(2)
  );

  return {
    subtotal,
    billDiscount,
    roundOff,
    grandTotal,
  };
}

export function billingReducer(state, action) {
  switch (action.type) {
    // =====================================
    // CUSTOMER
    // =====================================

    case "SET_CUSTOMER":
      return {
        ...state,
        customer: {
          ...state.customer,
          ...action.payload,
        },
      };

    case "SET_SCHOOL":
      return {
        ...state,
        selectedSchool: action.payload,
        customer: {
          ...state.customer,
          school: action.payload,
        },
      };

    // =====================================
    // ADD PRODUCT
    // =====================================

    case "ADD_ITEM": {
      const existing = state.items.find(
        (item) =>
          item.id === action.payload.id &&
          item.size === action.payload.size
      );

      let updatedItems;

      if (existing) {
        updatedItems = state.items.map((item) =>
          item.id === action.payload.id &&
          item.size === action.payload.size
            ? {
                ...item,
                qty: item.qty + 1,
              }
            : item
        );
      } else {
        updatedItems = [
          ...state.items,
          {
            ...action.payload,
            qty: action.payload.qty || 1,
            discount: action.payload.discount || 0,
            status:
              action.payload.status || "Delivered",
          },
        ];
      }

      return {
        ...state,
        items: updatedItems,
        ...calculateTotals(
          updatedItems,
          state.billDiscount
        ),
      };
    }

    // =====================================
    // QUANTITY
    // =====================================

    case "UPDATE_ITEM_QTY": {
      const updatedItems = state.items.map((item) =>
        item.id === action.payload.id
          ? {
              ...item,
              qty: Number(action.payload.qty),
            }
          : item
      );

      return {
        ...state,
        items: updatedItems,
        ...calculateTotals(
          updatedItems,
          state.billDiscount
        ),
      };
    }

    // =====================================
    // SIZE CHANGE
    // =====================================

    case "UPDATE_ITEM_SIZE": {
      const updatedItems = state.items.map((item) =>
        item.id === action.payload.oldId
          ? {
              ...action.payload.newItem,
              qty: item.qty,
              discount: item.discount,
              status: item.status,
            }
          : item
      );

      return {
        ...state,
        items: updatedItems,
        ...calculateTotals(
          updatedItems,
          state.billDiscount
        ),
      };
    }

    // =====================================
    // STATUS
    // =====================================

    case "UPDATE_ITEM_STATUS": {
      const updatedItems = state.items.map((item) =>
        item.id === action.payload.id
          ? {
              ...item,
              status: action.payload.status,
            }
          : item
      );

      return {
        ...state,
        items: updatedItems,
      };
    }

    // =====================================
    // REMOVE
    // =====================================

    case "REMOVE_ITEM": {
      const updatedItems = state.items.filter(
        (item) => item.id !== action.payload
      );

      return {
        ...state,
        items: updatedItems,
        ...calculateTotals(
          updatedItems,
          state.billDiscount
        ),
      };
    }

    // =====================================
    // DISCOUNT
    // =====================================

    case "SET_DISCOUNT":
      return {
        ...state,
        ...calculateTotals(
          state.items,
          action.payload
        ),
      };

    // =====================================
    // PAYMENT
    // =====================================

    case "SET_PAYMENT":
      return {
        ...state,
        paidAmount: Number(
          action.payload.paidAmount || 0
        ),
        paymentMode:
          action.payload.paymentMode,

        balance:
          Number(state.grandTotal) -
          Number(action.payload.paidAmount || 0),
      };

    // =====================================
    // TOTALS
    // =====================================

    case "SET_TOTALS":
      return {
        ...state,
        ...action.payload,
      };

    // =====================================
    // INVOICE
    // =====================================

    case "SET_INVOICE_NO":
      return {
        ...state,
        invoiceNo: action.payload,
      };

    // =====================================
    // CLEAR
    // =====================================

    case "CLEAR_BILL":
      return {
        ...initialState,
      };

    default:
      return state;
  }
}