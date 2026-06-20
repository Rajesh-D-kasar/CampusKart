import API from "./axiosConfig";

export const getCart = async () => {
  const response = await API.get("/cart");
  return response.data;
};

export const addCartItem = async (productId, quantity = 1) => {
  const response = await API.post("/cart/items", {
    product_id: productId,
    quantity,
  });
  return response.data;
};

export const updateCartItem = async (productId, quantity) => {
  const response = await API.patch(`/cart/items/${productId}`, { quantity });
  return response.data;
};

export const removeCartItem = async (productId) => {
  const response = await API.delete(`/cart/items/${productId}`);
  return response.data;
};

export const clearServerCart = async () => {
  const response = await API.delete("/cart");
  return response.data;
};
