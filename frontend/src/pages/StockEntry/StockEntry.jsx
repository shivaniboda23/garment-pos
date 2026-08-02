import { useState } from "react";

import StockEntryForm from "./StockEntryForm";
import StockEntryTable from "./StockEntryTable";

import { createStockEntry } from "../../services/stockService";

export default function StockEntry() {
  const [source, setSource] = useState("K");

  const [referenceName, setReferenceName] = useState("");

  const [remarks, setRemarks] = useState("");

  const [items, setItems] = useState([]);

  // =====================================
  // SAVE STOCK ENTRY
  // =====================================

  const saveStockEntry = async () => {
    if (items.length === 0) {
      alert("Please add at least one product.");
      return;
    }

    try {
      await createStockEntry({
        source,
        reference_name: referenceName,
        remarks,
        items,
      });

      alert("Stock Entry Saved Successfully.");

      // Reset Form
      setItems([]);
      setReferenceName("");
      setRemarks("");
      setSource("K");

    } catch (err) {
      console.error(err);

      alert("Failed to save stock entry.");
    }
  };

  return (
    <div className="p-6 space-y-6">

      <div className="flex justify-between items-center">

        <h1 className="text-3xl font-bold text-blue-700">
          Stock Entry
        </h1>

        <button
          onClick={saveStockEntry}
          className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold"
        >
          Save Stock Entry
        </button>

      </div>

      <StockEntryForm
        source={source}
        setSource={setSource}
        referenceName={referenceName}
        setReferenceName={setReferenceName}
        remarks={remarks}
        setRemarks={setRemarks}
      />

      <StockEntryTable
        source={source}
        items={items}
        setItems={setItems}
      />

    </div>
  );
}