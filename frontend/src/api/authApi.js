import API from "./axiosConfig";

export const registerUser = async (userData) => {
  const response = await API.post("/auth/register", userData);
  return response.data;
};

export const loginUser = async (loginData) => {
  const response = await API.post("/auth/login", loginData);
  return response.data;
};

export const requestOtp = async (otpData) => {
  const response = await API.post("/auth/otp/request", otpData);
  return response.data;
};

export const verifyOtp = async (otpData) => {
  const response = await API.post("/auth/otp/verify", otpData);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await API.get("/auth/me");
  return response.data;
};
