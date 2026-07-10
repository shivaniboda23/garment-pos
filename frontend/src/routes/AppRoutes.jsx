import { BrowserRouter, Routes, Route } from "react-router-dom";
import Billing from "../pages/Billing/Billing";

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Billing />} />
      </Routes>
    </BrowserRouter>
  );
}