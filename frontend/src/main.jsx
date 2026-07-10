import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

import { BillingProvider } from "./context/BillingContext";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BillingProvider>
      <App />
    </BillingProvider>
  </React.StrictMode>
);