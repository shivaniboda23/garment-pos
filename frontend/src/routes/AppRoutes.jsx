import { BrowserRouter, Routes, Route } from "react-router-dom";

import Billing from "../pages/Billing/Billing";
import BulkProduct from "../pages/Products/BulkProduct";

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Billing />} />

        <Route
          path="/products/bulk"
          element={<BulkProduct />}
        />
      </Routes>
    </BrowserRouter>
  );
}