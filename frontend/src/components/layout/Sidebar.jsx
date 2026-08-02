import { motion } from "framer-motion";
import { NavLink } from "react-router-dom";
import {
  ChevronLeft,
  ChevronRight,
  ShoppingBag,
  HardDrive,
} from "lucide-react";

import { menu } from "./navigation/menu";

export default function Sidebar({ collapsed, setCollapsed }) {
  return (
    <motion.aside
      animate={{
        width: collapsed ? 90 : 280,
      }}
      transition={{
        duration: 0.3,
      }}
      className="h-screen sticky top-0 bg-white border-r border-slate-200 shadow-xl flex flex-col"
    >
      {/* ---------------- Logo ---------------- */}

      <div className="relative p-6 flex items-center justify-between">

        <div className="flex items-center gap-3 overflow-hidden">

          <div
            className="
            w-14
            h-14
            rounded-2xl
            bg-gradient-to-br
            from-blue-600
            to-indigo-600
            flex
            items-center
            justify-center
            shadow-lg
            "
          >
            <ShoppingBag className="text-white" size={28} />
          </div>

          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <h1 className="text-xl font-bold text-slate-800">
                Bhavani ERP
              </h1>

              <p className="text-sm text-slate-500">
                Smart Garment Management
              </p>
            </motion.div>
          )}
        </div>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="
          absolute
          -right-4
          top-8
          bg-white
          shadow-lg
          border
          rounded-full
          p-2
          hover:bg-blue-600
          hover:text-white
          transition
          "
        >
          {collapsed ? (
            <ChevronRight size={18} />
          ) : (
            <ChevronLeft size={18} />
          )}
        </button>
      </div>

      {/* ---------------- Menu ---------------- */}

      <div className="flex-1 px-4 mt-4">

        <p
          className={`text-xs uppercase text-gray-400 mb-3 ${
            collapsed && "hidden"
          }`}
        >
          Main Menu
        </p>

        <div className="space-y-2">

          {menu.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) =>
                  `
                  flex
                  items-center
                  gap-4
                  px-4
                  py-3
                  rounded-2xl
                  transition-all
                  duration-300
                  group

                  ${
                    isActive
                      ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg"
                      : "text-slate-600 hover:bg-slate-100"
                  }
                  `
                }
              >
                <Icon
                  size={22}
                  className="group-hover:scale-110 transition"
                />

                {!collapsed && (
                  <span className="font-medium">
                    {item.name}
                  </span>
                )}
              </NavLink>
            );
          })}
        </div>
      </div>

      {/* ---------------- Storage Card ---------------- */}

      {!collapsed && (
        <div className="mx-4 mb-5">

          <div
            className="
            rounded-3xl
            bg-gradient-to-br
            from-blue-600
            to-indigo-700
            p-5
            text-white
            shadow-xl
            "
          >
            <div className="flex justify-between items-center">

              <HardDrive />

              <span className="text-sm">
                Storage
              </span>
            </div>

            <h2 className="text-3xl font-bold mt-3">
              72%
            </h2>

            <div className="mt-4 h-3 bg-white/30 rounded-full overflow-hidden">

              <div
                className="
                h-full
                bg-white
                rounded-full
                "
                style={{
                  width: "72%",
                }}
              />

            </div>

            <p className="text-sm mt-3 text-blue-100">
              Database usage
            </p>
          </div>
        </div>
      )}

      {/* ---------------- User ---------------- */}

      <div
        className="
        border-t
        p-5
        flex
        items-center
        gap-3
        "
      >
        <img
          src="https://ui-avatars.com/api/?name=Shivani&background=2563eb&color=fff"
          alt="user"
          className="w-12 h-12 rounded-full"
        />

        {!collapsed && (
          <div>

            <h3 className="font-semibold">
              Shivani
            </h3>

            <p className="text-sm text-gray-500">
              Administrator
            </p>

          </div>
        )}
      </div>
    </motion.aside>
  );
}