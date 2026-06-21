import API from "./axiosConfig";

export async function createSupportTicket(payload) {
  const response = await API.post("/support/tickets", payload);
  return response.data;
}

export async function getSupportTickets() {
  const response = await API.get("/support/tickets");
  return response.data;
}

export async function addSupportMessage(ticketId, payload) {
  const response = await API.post(`/support/tickets/${ticketId}/messages`, payload);
  return response.data;
}
