import API from "./axiosConfig";

export const placeOrder = async (orderData) => {
  const response = await API.post("/orders", orderData);
  return response.data;
};
