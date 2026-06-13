import API from "./axiosConfig";

export const addToCart = async (productId, quantity) => {
  const response = await API.post("/cart/add", {
    product_id: productId,
    quantity: quantity,
  });

  return response.data;
};
