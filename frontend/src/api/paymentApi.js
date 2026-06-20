import API from "./axiosConfig";

export const createRazorpayOrder = async (paymentData) => {
  const response = await API.post("/payments/razorpay/orders", paymentData);
  return response.data;
};

export const verifyRazorpayPayment = async (paymentData) => {
  const response = await API.post("/payments/razorpay/verify", paymentData);
  return response.data;
};
