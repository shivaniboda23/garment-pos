const products = [
  {
    name: "School Shirt M",
    stock: 2,
  },
  {
    name: "Pant 30",
    stock: 1,
  },
  {
    name: "Blazer XL",
    stock: 3,
  },
];

export default function LowStock() {
  return (
    <div className="bg-white rounded-3xl shadow-xl p-6">

      <h2 className="text-xl font-bold mb-5">
        Low Stock
      </h2>

      {products.map((item) => (
        <div
          key={item.name}
          className="flex justify-between py-3 border-b"
        >
          <span>{item.name}</span>

          <span className="text-red-500 font-bold">
            {item.stock}
          </span>
        </div>
      ))}

    </div>
  );
}