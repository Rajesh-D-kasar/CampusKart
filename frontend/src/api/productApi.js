import API from "./axiosConfig";

export const getProducts = async (params = {}) => {
  const response = await API.get("/products", { params });
  return response.data;
};

export const getCategories = async () => {
  const response = await API.get("/products/categories");
  return response.data;
};
