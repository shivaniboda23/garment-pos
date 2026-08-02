import { BrowserRouter, Routes, Route } from "react-router-dom";

import AppLayout from "./components/layout/AppLayout";

import Dashboard from "./pages/Dashboard/Dashboard";
import Billing from "./pages/Billing/Billing";

function EmptyPage({ title }) {
  return (
    <div className="bg-white rounded-3xl shadow-xl p-12">
      <h1 className="text-3xl font-bold">{title}</h1>

      <p className="text-slate-500 mt-3">
        Coming Soon...
      </p>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>

      <Routes>

        <Route element={<AppLayout />}>

          <Route
            path="/"
            element={<Dashboard />}
          />

          <Route
            path="/billing"
            element={<Billing />}
          />

          <Route
            path="/products"
            element={<EmptyPage title="Products" />}
          />

          <Route
            path="/inventory"
            element={<EmptyPage title="Inventory" />}
          />

          <Route
            path="/customers"
            element={<EmptyPage title="Customers" />}
          />

          <Route
            path="/schools"
            element={<EmptyPage title="Schools" />}
          />

          <Route
            path="/suppliers"
            element={<EmptyPage title="Suppliers" />}
          />

          <Route
            path="/reports"
            element={<EmptyPage title="Reports" />}
          />

          <Route
            path="/settings"
            element={<EmptyPage title="Settings" />}
          />

        </Route>

      </Routes>

    </BrowserRouter>
  );
}