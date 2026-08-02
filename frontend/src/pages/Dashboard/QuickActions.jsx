import { Plus, Package, Users } from "lucide-react";

export default function QuickActions() {
  const actions = [
    {
      title: "New Bill",
      icon: Plus,
      color: "bg-blue-600",
    },
    {
      title: "Add Product",
      icon: Package,
      color: "bg-green-600",
    },
    {
      title: "Add Customer",
      icon: Users,
      color: "bg-purple-600",
    },
  ];

  return (
    <div className="bg-white rounded-3xl shadow-xl p-6">

      <h2 className="text-xl font-bold mb-5">
        Quick Actions
      </h2>

      <div className="space-y-4">

        {actions.map((action) => {
          const Icon = action.icon;

          return (
            <button
              key={action.title}
              className={`${action.color}
              w-full
              text-white
              rounded-2xl
              p-4
              flex
              items-center
              gap-3
              hover:scale-105
              transition`}
            >
              <Icon size={20} />

              {action.title}
            </button>
          );
        })}

      </div>

    </div>
  );
}