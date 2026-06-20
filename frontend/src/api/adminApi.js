import API from "./axiosConfig";

export const getAdminSummary = async () => {
  const response = await API.get("/admin/summary");
  return response.data;
};

export const getAdminOrders = async () => {
  const response = await API.get("/admin/orders");
  return response.data;
};

export const updateAdminOrderStatus = async (orderId, status) => {
  const response = await API.patch(`/admin/orders/${orderId}/status`, {
    status,
  });
  return response.data;
};

export const getAdminCategories = async () => {
  const response = await API.get("/admin/categories");
  return response.data;
};

export const createAdminCategory = async (categoryData) => {
  const response = await API.post("/admin/categories", categoryData);
  return response.data;
};

export const updateAdminCategory = async (categoryId, categoryData) => {
  const response = await API.patch(`/admin/categories/${categoryId}`, categoryData);
  return response.data;
};

export const getAdminProducts = async () => {
  const response = await API.get("/admin/products");
  return response.data;
};

export const createAdminProduct = async (productData) => {
  const response = await API.post("/admin/products", productData);
  return response.data;
};

export const updateAdminProduct = async (productId, productData) => {
  const response = await API.patch(`/admin/products/${productId}`, productData);
  return response.data;
};

export const getAdminInventory = async () => {
  const response = await API.get("/admin/inventory");
  return response.data;
};

export const updateAdminInventory = async (productId, inventoryData) => {
  const response = await API.patch(`/admin/inventory/${productId}`, inventoryData);
  return response.data;
};
