import { motion } from "framer-motion";

export default function StatCard({
  title,
  value,
  icon: Icon,
  color,
}) {
  return (
    <motion.div
      whileHover={{
        y: -8,
        scale: 1.02,
      }}
      className="bg-white rounded-3xl shadow-xl p-6"
    >
      <div
        className={`w-14 h-14 rounded-2xl bg-gradient-to-r ${color}
        flex items-center justify-center text-white`}
      >
        <Icon size={28} />
      </div>

      <p className="text-slate-500 mt-5">{title}</p>

      <h2 className="text-3xl font-bold mt-2">
        {value}
      </h2>
    </motion.div>
  );
}