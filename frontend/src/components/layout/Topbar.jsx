import { motion } from "framer-motion";
import {
  Search,
  Bell,
  Moon,
  Command,
  CalendarDays,
  ChevronDown,
} from "lucide-react";

export default function Topbar() {
  const today = new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <motion.header
      initial={{
        y: -30,
        opacity: 0,
      }}
      animate={{
        y: 0,
        opacity: 1,
      }}
      transition={{
        duration: 0.4,
      }}
      className="
      sticky
      top-0
      z-40
      backdrop-blur-xl
      bg-white/80
      border-b
      border-slate-200
      "
    >
      <div className="flex items-center justify-between px-8 py-5">

        {/* Left */}

        <div>

          <h1 className="text-3xl font-bold text-slate-800">
            Dashboard
          </h1>

          <div className="flex items-center gap-2 mt-1 text-slate-500">

            <CalendarDays size={16} />

            <span className="text-sm">
              {today}
            </span>

          </div>

        </div>

        {/* Right */}

        <div className="flex items-center gap-5">

          {/* Search */}

          <div
            className="
            hidden
            lg:flex
            items-center
            bg-slate-100
            rounded-2xl
            px-4
            py-3
            w-[380px]
            "
          >
            <Search
              size={18}
              className="text-slate-400"
            />

            <input
              placeholder="Search invoices, customers, products..."
              className="
              flex-1
              bg-transparent
              outline-none
              px-3
              text-sm
              "
            />

            <div
              className="
              flex
              items-center
              gap-1
              bg-white
              rounded-lg
              px-2
              py-1
              text-xs
              text-slate-500
              shadow
              "
            >
              <Command size={14} />

              K
            </div>
          </div>

          {/* Notification */}

          <button
            className="
            w-12
            h-12
            rounded-2xl
            bg-white
            shadow-md
            hover:bg-blue-600
            hover:text-white
            transition
            flex
            items-center
            justify-center
            "
          >
            <Bell size={20} />
          </button>

          {/* Dark Mode */}

          <button
            className="
            w-12
            h-12
            rounded-2xl
            bg-white
            shadow-md
            hover:bg-indigo-600
            hover:text-white
            transition
            flex
            items-center
            justify-center
            "
          >
            <Moon size={20} />
          </button>

          {/* Profile */}

          <button
            className="
            flex
            items-center
            gap-3
            bg-white
            rounded-2xl
            shadow-md
            px-4
            py-2
            hover:shadow-xl
            transition
            "
          >
            <img
              src="https://ui-avatars.com/api/?name=Shivani&background=2563EB&color=fff"
              alt="profile"
              className="w-11 h-11 rounded-full"
            />

            <div className="hidden md:block text-left">

              <h3 className="font-semibold text-slate-800">
                Shivani
              </h3>

              <p className="text-xs text-slate-500">
                Administrator
              </p>

            </div>

            <ChevronDown
              size={18}
              className="text-slate-500"
            />

          </button>

        </div>

      </div>
    </motion.header>
  );
}