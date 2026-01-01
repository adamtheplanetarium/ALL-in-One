import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth API
export const authAPI = {
  login: (password) => api.post('/auth/login', { password }),
  logout: () => api.post('/auth/logout'),
  checkAuth: () => api.get('/auth/check'),
};

// SMTP API
export const smtpAPI = {
  getServers: () => api.get('/smtp'),
  addServer: (server) => api.post('/smtp', server),
  deleteServer: (host, username) => api.delete('/smtp', { data: { host, username } }),
  testServer: (server) => api.post('/smtp/test', server),
  bulkUpdate: (servers) => api.put('/smtp/bulk', { servers }),
};

// Email API
export const emailAPI = {
  getRecipients: () => api.get('/emails/recipients'),
  getFromEmails: () => api.get('/emails/from'),
  getStatistics: () => api.get('/emails/statistics'),
  uploadRecipients: (emails) => api.post('/emails/recipients', { emails }),
  uploadFromEmails: (emails) => api.post('/emails/from', { emails }),
  clearRecipients: () => api.delete('/emails/recipients'),
  clearFromEmails: () => api.delete('/emails/from'),
};

// Campaign API
export const campaignAPI = {
  start: () => api.post('/campaign/start'),
  stop: () => api.post('/campaign/stop'),
  getState: () => api.get('/campaign/state'),
  getStatistics: () => api.get('/campaign/statistics'),
  getLogs: (limit) => api.get('/campaign/logs', { params: { limit } }),
  clearLogs: () => api.delete('/campaign/logs'),
  getConfig: () => api.get('/campaign/config'),
  updateConfig: (section, key, value) => api.put('/campaign/config', { section, key, value }),
  updateFullConfig: (config) => api.put('/campaign/config/full', { config }),
};

// Template API
export const templateAPI = {
  get: () => api.get('/template'),
  save: (content, filename) => api.post('/template', { content, filename }),
  getVariables: () => api.get('/template/variables'),
};

export default api;
