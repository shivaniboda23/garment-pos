import {
  LayoutDashboard,
  Receipt,
  Shirt,
  Boxes,
  Users,
  GraduationCap,
  Truck,
  BarChart3,
  Settings,
} from "lucide-react";

export const menu = [
  {
    name: "Dashboard",
    icon: LayoutDashboard,
    path: "/",
  },
  {
    name: "Billing",
    icon: Receipt,
    path: "/billing",
  },
  {
    name: "Products",
    icon: Shirt,
    path: "/products",
  },
  {
    name: "Inventory",
    icon: Boxes,
    path: "/inventory",
  },
  {
    name: "Customers",
    icon: Users,
    path: "/customers",
  },
  {
    name: "Schools",
    icon: GraduationCap,
    path: "/schools",
  },
  {
    name: "Suppliers",
    icon: Truck,
    path: "/suppliers",
  },
  {
    name: "Reports",
    icon: BarChart3,
    path: "/reports",
  },
  {
    name: "Settings",
    icon: Settings,
    path: "/settings",
  },
];