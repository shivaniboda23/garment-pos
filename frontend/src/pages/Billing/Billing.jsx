import { useEffect } from "react";
import { useBilling } from "../../context/BillingContext";
import { calculateBill } from "../../utils/billingCalculator";

import BillingHeader from "./components/BillingHeader";
import CustomerPanel from "./components/CustomerPanel";
import BillingProductSearch from "./components/BillingProductSearch";
import BillingProductTable from "./components/BillingProductTable";
import TotalsCard from "./components/TotalsCard";
import PaymentPanel from "./components/PaymentPanel";
import ActionButtons from "./components/ActionButtons";
import InvoicePreview from "./components/InvoicePreview";

export default function Billing() {
  const { state, dispatch } = useBilling();

  useEffect(() => {
    const totals = calculateBill(
      state.items,
      state.billDiscount
    );

    dispatch({
      type: "SET_TOTALS",
      payload: totals,
    });
  }, [state.items, state.billDiscount, dispatch]);

  return (
    <>
    
      <div className="min-h-screen bg-gray-100">
        <div className="max-w-[1600px] mx-auto px-8 py-6 space-y-6">

          <BillingHeader />

          <CustomerPanel />

          <BillingProductSearch />

          <BillingProductTable />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <TotalsCard />
            <PaymentPanel />
          </div>

          <ActionButtons />

          <InvoicePreview />

        </div>
      </div>
    </>
  );
}