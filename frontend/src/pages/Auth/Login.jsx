import { useState } from "react";
import AuthLayout from "../../components/layout/AuthLayout";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <AuthLayout>
      <div className="bg-white shadow-xl rounded-2xl w-[420px] p-10">
        <h1 className="text-3xl font-bold text-center text-blue-600">
          RetailFlow POS
        </h1>

        <p className="text-center text-gray-500 mt-2 mb-8">
          Smart Billing & Inventory Management
        </p>

        <Input
          label="Email"
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <Input
          label="Password"
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <Button>Login</Button>
      </div>
    </AuthLayout>
  );
}