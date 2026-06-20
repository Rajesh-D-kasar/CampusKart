import API from "./axiosConfig";

export const getOffers = async () => {
  const response = await API.get("/offers");
  return response.data;
};

export const previewCoupon = async ({ code, subtotal, deliveryFee }) => {
  const response = await API.post("/offers/coupons/preview", {
    code,
    subtotal,
    delivery_fee: deliveryFee,
  });
  return response.data;
};
