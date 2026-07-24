import axios from 'axios';

const API_BASE_URL = 'http://localhost:8080';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercept requests to add JWT token if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Normalize FastAPI error shapes into a human-readable message
// FastAPI can return: { detail: "string" } | { detail: [{msg, loc}] } | plain text
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const data = error.response.data;
      let message = `Server error (${error.response.status})`;

      if (typeof data?.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data?.detail)) {
        // Pydantic validation errors — join all messages
        message = data.detail
          .map(d => `${d.loc?.slice(-1)[0] ?? 'field'}: ${d.msg}`)
          .join(' | ');
      } else if (typeof data?.message === 'string') {
        message = data.message;
      }

      error.userMessage = message;
    } else if (error.request) {
      error.userMessage = 'No response from server. Is the backend running?';
    } else {
      error.userMessage = error.message || 'An unexpected error occurred.';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) => api.post('/api/auth/login', { username, password }),
  register: (data) => api.post('/api/auth/register', data),
  getMe: () => api.get('/api/auth/me'),
};

export const clinicalAPI = {
  extractNote: (content) => api.post('/api/extract', { content }),
};

export const doctorAPI = {
  getDashboard: () => api.get('/api/doctor/dashboard'),
  getReviewQueue: () => api.get('/api/doctor/review-queue'),
  takeReviewAction: (id, action, reviewer, newValue = null) =>
    api.post(`/api/doctor/review/${id}/action`, { action, reviewer, new_value: newValue }),
  approveAll: () => api.post('/api/doctor/review-queue/approve-all'),
  getPatientHistory: (search = '') => api.get(`/api/doctor/patient-history?search=${search}`),
  exportJSON: (sessionId) => api.get(`/api/doctor/export/json/${sessionId}`),
  exportPDF: (sessionId) => api.get(`/api/doctor/export/pdf/${sessionId}`, { responseType: 'blob' }),
};

// Removes invalid JSON control characters (ASCII 0x00–0x08, 0x0B–0x0C, 0x0E–0x1F)
// while preserving normal whitespace: space (0x20), tab (0x09), newline (0x0A), carriage return (0x0D)
const sanitizeText = (text) =>
  text.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '');

export const patientAPI = {
  submitNote: (clinical_note) =>
    api.post('/api/patient/submit-note', { clinical_note: sanitizeText(clinical_note) }),
  getHistory: () => api.get('/api/patient/history'),
  getSummary: (sessionId) => api.get(`/api/patient/summary/${sessionId}`),
  downloadPDF: (sessionId) => api.get(`/api/patient/download-pdf/${sessionId}`, { responseType: 'blob' }),
};

/**
 * Trigger an authenticated PDF blob download.
 * Pass the axios response (responseType:'blob') and a filename.
 */
export const triggerBlobDownload = (response, filename) => {
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export default api;
