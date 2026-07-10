import { createContext, useContext, useReducer } from "react";
import { billingReducer, initialState } from "../reducers/billingReducer";

const BillingContext = createContext();

export function BillingProvider({ children }) {
  const [state, dispatch] = useReducer(
    billingReducer,
    initialState
  );

  return (
    <BillingContext.Provider
      value={{
        state,
        dispatch,
      }}
    >
      {children}
    </BillingContext.Provider>
  );
}

export function useBilling() {
  return useContext(BillingContext);
}