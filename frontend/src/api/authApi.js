import API from "./axiosConfig";

export const registerUser = async (userData) => {
  const response = await API.post("/register", userData);
  return response.data;
};

export const loginUser = async (loginData) => {
  const response = await API.post("/login", loginData);
  return response.data;
};
