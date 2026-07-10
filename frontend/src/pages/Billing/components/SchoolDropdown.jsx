import { useEffect, useState } from "react";
import { useBilling } from "../../../context/BillingContext";
import { getSchools } from "../../../services/schoolService";

export default function SchoolDropdown() {
  const { state, dispatch } = useBilling();

  const [schools, setSchools] = useState([]);

  useEffect(() => {
    loadSchools();
  }, []);

  const loadSchools = async () => {
    try {
      const data = await getSchools();
      setSchools(data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="mt-4">
      <label className="block mb-2 font-semibold">
        School
      </label>

      <select
        className="w-full border rounded-lg p-3"
        value={state.selectedSchool?.id || ""}
        onChange={(e) => {
          const school = schools.find(
            (s) => s.id === Number(e.target.value)
          );

          dispatch({
            type: "SET_SCHOOL",
            payload: school || null,
          });
        }}
      >
        <option value="">All Schools</option>

        {schools.map((school) => (
          <option key={school.id} value={school.id}>
            {school.school_name}
          </option>
        ))}
      </select>
    </div>
  );
}