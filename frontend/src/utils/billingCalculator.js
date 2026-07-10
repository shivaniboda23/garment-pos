export function calculateBill(items, billDiscount = 0) {
  let subtotal = 0;

  items.forEach((item) => {
    const qty = Number(item.qty || 0);
    const price = Number(item.price || 0);
    const discount = Number(item.discount || 0);

    const amount = qty * price;
    const discountAmount = (amount * discount) / 100;

    subtotal += amount - discountAmount;
  });

  const totalBeforeRound = subtotal - Number(billDiscount || 0);

  const grandTotal = Math.round(totalBeforeRound);

  const roundOff = Number(
    (grandTotal - totalBeforeRound).toFixed(2)
  );

  return {
    subtotal,
    billDiscount,
    roundOff,
    grandTotal,
  };
}