import API from "./axiosConfig";

export const getAddresses = async () => {
  const response = await API.get("/addresses");
  return response.data;
};

export const createAddress = async (addressData) => {
  const response = await API.post("/addresses", addressData);
  return response.data;
};

export const updateAddress = async (addressId, addressData) => {
  const response = await API.patch(`/addresses/${addressId}`, addressData);
  return response.data;
};

export const deleteAddress = async (addressId) => {
  await API.delete(`/addresses/${addressId}`);
};
