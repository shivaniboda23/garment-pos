import AuthLayout from "../../components/layout/AuthLayout";

export default function Login() {
  return (
    <AuthLayout>
      <div className="bg-white shadow-xl rounded-2xl w-[420px] p-10">
        <h1 className="text-3xl font-bold text-center text-blue-600">
          RetailFlow POS
        </h1>

        <p className="text-center text-gray-500 mt-2">
          Smart Billing & Inventory Management
        </p>

        <div className="mt-8">
          <label className="block font-medium">Email</label>

          <input
            type="email"
            placeholder="Enter email"
            className="w-full mt-2 border rounded-lg px-4 py-3"
          />
        </div>

        <div className="mt-5">
          <label className="block font-medium">Password</label>

          <input
            type="password"
            placeholder="Enter password"
            className="w-full mt-2 border rounded-lg px-4 py-3"
          />
        </div>

        <button className="w-full mt-8 bg-blue-600 text-white py-3 rounded-xl hover:bg-blue-700">
          Login
        </button>
      </div>
    </AuthLayout>
  );
}