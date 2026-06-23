import API from "./axiosConfig";

export const getWallet = async () => {
  const response = await API.get("/wallet");
  return response.data;
};
