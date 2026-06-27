const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

const dateTimeFormatter = new Intl.DateTimeFormat("en-IN", {
  dateStyle: "medium",
  timeStyle: "short",
});

const PAYMENT_METHOD_LABELS = {
  cash_on_delivery: "Cash on delivery",
  upi: "UPI (demo)",
  card: "Card (demo)",
  razorpay: "Razorpay",
};

export function formatCurrency(value) {
  return inrFormatter.format(value ?? 0);
}

export function formatDateTime(dateValue, fallback = "Updating soon") {
  if (!dateValue) return fallback;
  return dateTimeFormatter.format(new Date(dateValue));
}

export function formatLabel(value, fallback = "Updating") {
  if (!value) return fallback;
  return String(value).replaceAll("_", " ");
}

export function formatPaymentMethod(method) {
  return PAYMENT_METHOD_LABELS[method] || formatLabel(method, "Payment");
}
