import API from "./axiosConfig";

export const getProducts = async (params = {}) => {
  const response = await API.get("/products", { params });
  return response.data;
};

export const getProduct = async (productId) => {
  const response = await API.get(`/products/${productId}`);
  return response.data;
};

export const getProductRecommendations = async (productId) => {
  const response = await API.get(`/products/${productId}/recommendations`);
  return response.data;
};

export const getProductSuggestions = async (query = "") => {
  const response = await API.get("/products/suggestions", {
    params: query ? { q: query } : {},
  });
  return response.data;
};

export const getCategories = async () => {
  const response = await API.get("/products/categories");
  return response.data;
};
