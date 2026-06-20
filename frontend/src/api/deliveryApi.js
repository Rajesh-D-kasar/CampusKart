import API from "./axiosConfig";

export const getDeliveryOrders = async () => {
  const response = await API.get("/delivery/orders");
  return response.data;
};

export const getDeliverySummary = async () => {
  const response = await API.get("/delivery/summary");
  return response.data;
};

export const updateDeliveryOrderStatus = async (orderId, status) => {
  const response = await API.patch(`/delivery/orders/${orderId}/status`, {
    status,
  });
  return response.data;
};
