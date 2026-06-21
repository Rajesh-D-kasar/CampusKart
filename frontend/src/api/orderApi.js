import API from "./axiosConfig";

export const placeOrder = async (orderData) => {
  const response = await API.post("/orders", orderData);
  return response.data;
};

export const getOrders = async () => {
  const response = await API.get("/orders");
  return response.data;
};

export const getOrder = async (orderId) => {
  const response = await API.get(`/orders/${orderId}`);
  return response.data;
};

export const cancelOrder = async (orderId, reason) => {
  const response = await API.patch(`/orders/${orderId}/cancel`, { reason });
  return response.data;
};

export const getOrderInvoice = async (orderId) => {
  const response = await API.get(`/orders/${orderId}/invoice`);
  return response.data;
};
