export default function StockEntryForm({
  source,
  setSource,
  referenceName,
  setReferenceName,
  remarks,
  setRemarks,
}) {
  return (
    <div className="bg-white rounded-xl shadow-lg p-6">

      <h2 className="text-xl font-bold text-blue-700 mb-6">
        Stock Entry Details
      </h2>

      <div className="grid md:grid-cols-3 gap-5">

        {/* ===================================== */}
        {/* SOURCE */}
        {/* ===================================== */}

        <div>

          <label className="block mb-2 font-semibold">
            Source
          </label>

          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="w-full border rounded-lg p-3"
          >
            <option value="K">
              K - Tailor (Own Manufacturing)
            </option>

            <option value="R">
              R - Ready Made Manufacturer
            </option>

          </select>

        </div>

        {/* ===================================== */}
        {/* REFERENCE NAME */}
        {/* ===================================== */}

        <div>

          <label className="block mb-2 font-semibold">

            {source === "K"
              ? "Tailor Name"
              : "Manufacturer Name"}

          </label>

          <input
            type="text"
            value={referenceName}
            onChange={(e) =>
              setReferenceName(e.target.value)
            }
            placeholder={
              source === "K"
                ? "Enter Tailor Name"
                : "Enter Manufacturer Name"
            }
            className="w-full border rounded-lg p-3"
          />

        </div>

        {/* ===================================== */}
        {/* REMARKS */}
        {/* ===================================== */}

        <div>

          <label className="block mb-2 font-semibold">
            Remarks
          </label>

          <input
            type="text"
            value={remarks}
            onChange={(e) =>
              setRemarks(e.target.value)
            }
            placeholder="Optional Remarks"
            className="w-full border rounded-lg p-3"
          />

        </div>

      </div>

      {/* ===================================== */}
      {/* INFO BOX */}
      {/* ===================================== */}

      <div className="mt-6 rounded-lg bg-blue-50 border border-blue-200 p-4">

        <p className="text-sm text-gray-700">

          <span className="font-bold text-blue-700">
            K
          </span>{" "}
          = Own Manufacturing (Tailor)

        </p>

        <p className="text-sm text-gray-700 mt-1">

          <span className="font-bold text-green-700">
            R
          </span>{" "}
          = Ready Made Manufacturer

        </p>

      </div>

    </div>
  );
}