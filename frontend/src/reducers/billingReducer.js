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

    const amount = qty * price;
    const discountAmount = (amount * discount) / 100;

    subtotal += amount - discountAmount;
  });

  const totalBeforeRound =
    subtotal - Number(billDiscount || 0);

  const grandTotal = Math.round(totalBeforeRound);

  const roundOff = Number(
    (grandTotal - totalBeforeRound).toFixed(2)
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
      };

    case "ADD_ITEM": {
      const existing = state.items.find(
        (item) =>
          item.id === action.payload.id &&
          item.size === action.payload.size &&
          item.color === action.payload.color
      );

      let updatedItems;

      if (existing) {
        updatedItems = state.items.map((item) =>
          item.id === action.payload.id &&
          item.size === action.payload.size &&
          item.color === action.payload.color
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
          },
        ];
      }

      return {
        ...state,
        items: updatedItems,
        ...calculateTotals(updatedItems, state.billDiscount),
      };
    }

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
        ...calculateTotals(updatedItems, state.billDiscount),
      };
    }

    case "REMOVE_ITEM": {
      const updatedItems = state.items.filter(
        (item) => item.id !== action.payload
      );

      return {
        ...state,
        items: updatedItems,
        ...calculateTotals(updatedItems, state.billDiscount),
      };
    }

    case "SET_DISCOUNT":
      return {
        ...state,
        ...calculateTotals(state.items, action.payload),
      };

    case "SET_PAYMENT":
      return {
        ...state,
        paidAmount: Number(action.payload.paidAmount || 0),
        paymentMode: action.payload.paymentMode,
        balance: Number(action.payload.balance || 0),
      };

    case "SET_INVOICE_NO":
      return {
        ...state,
        invoiceNo: action.payload,
      };

    case "SET_TOTALS":
      return {
        ...state,
        ...action.payload,
      };

    case "CLEAR_BILL":
      return {
        ...initialState,
      };

    default:
      return state;
  }
}