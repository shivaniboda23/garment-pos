import { Receipt, CalendarDays, UserCircle2 } from "lucide-react";
import { useBilling } from "../../../context/BillingContext";

export default function BillingHeader() {
  const { state } = useBilling();

  return (
    <div className="rounded-2xl bg-gradient-to-r from-blue-700 via-blue-600 to-indigo-700 text-white shadow-xl p-6">

      <div className="flex flex-col lg:flex-row justify-between gap-5">

        <div>
          <h1 className="text-3xl font-bold">
            🏪 Bhavani Garments ERP
          </h1>

          <p className="text-blue-100 mt-2">
            Garments • Uniforms • Sports Wear
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">
            <div className="flex items-center gap-2">

              <Receipt size={18} />

              <span className="text-sm">
                Invoice
              </span>

            </div>

            <h2 className="font-bold text-xl mt-2">
              {state.invoiceNo || "NEW BILL"}
            </h2>

          </div>

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">

            <div className="flex items-center gap-2">

              <CalendarDays size={18} />

              <span className="text-sm">
                Date
              </span>

            </div>

            <h2 className="font-semibold mt-2">
              {new Date().toLocaleDateString()}
            </h2>

          </div>

          <div className="bg-white/10 rounded-xl p-4 backdrop-blur">

            <div className="flex items-center gap-2">

              <UserCircle2 size={18} />

              <span className="text-sm">
                Cashier
              </span>

            </div>

            <h2 className="font-semibold mt-2">
              Admin
            </h2>

          </div>

        </div>

      </div>

    </div>
  );
}