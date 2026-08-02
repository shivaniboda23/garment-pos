import { useState } from "react";
import { Outlet } from "react-router-dom";
import { motion } from "framer-motion";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-slate-100 flex overflow-hidden">

      {/* Sidebar */}
      <Sidebar
        collapsed={collapsed}
        setCollapsed={setCollapsed}
      />

      {/* Main Content */}
      <motion.div
        layout
        transition={{
          duration: 0.3,
        }}
        className="flex-1 flex flex-col overflow-hidden"
      >

        {/* Top Navigation */}
        <Topbar />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-8">

          <motion.div
            initial={{
              opacity: 0,
              y: 20,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              duration: 0.4,
            }}
            className="max-w-[1700px] mx-auto"
          >
            <Outlet />
          </motion.div>

        </main>

      </motion.div>

    </div>
  );
}