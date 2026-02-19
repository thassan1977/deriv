import axios from "axios";

const API_BASE = "http://localhost:8080/api/v1/dashboard";

export const getStats = () =>
  axios.get(`${API_BASE}/stats`);

export const getQueue = () =>
  axios.get(`${API_BASE}/queue`);

export const getCaseById = (caseId) =>
  axios.get(`${API_BASE}/cases/${caseId}`);

export const resolveCase = (caseId, decision, notes) =>
  axios.post(`${API_BASE}/cases/${caseId}/resolve`, {
    decision,
    notes
  });
