import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "../pages/Auth/Login";

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
      </Routes>
    </BrowserRouter>
  );
}