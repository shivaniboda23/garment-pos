import BulkProductForm from "./components/BulkProductForm";

export default function BulkProduct() {
  return (
    <div className="p-6">

      <div className="mb-6">

        <h1 className="text-3xl font-bold text-blue-700">
          Bulk Product Creation
        </h1>

        <p className="text-gray-600 mt-2">
          Create multiple product variants with one click.
        </p>

      </div>

      <BulkProductForm />

    </div>
  );
}