import type { AuthResponse, DashboardData, ReviewQueueItem, PatientHistoryRecord, ExtractionResponse } from '../types/api';

// Empty string = same origin → Vite proxy forwards /api/* → http://127.0.0.1:8080 (no CORS)
const BASE: string = import.meta.env.VITE_API_BASE_URL || '';

export function getAuthToken(): string | null  { return localStorage.getItem('access_token'); }
export function getRefreshToken(): string | null { return localStorage.getItem('refresh_token'); }
export function setAuthToken(access_token: string | null, refresh_token?: string | null) {
  if (access_token) localStorage.setItem('access_token', access_token);
  else localStorage.removeItem('access_token');
  if (refresh_token !== undefined) {
    if (refresh_token) localStorage.setItem('refresh_token', refresh_token);
    else localStorage.removeItem('refresh_token');
  }
}
export function getStoredUser(): any | null    { const u = localStorage.getItem('user_data'); return u ? JSON.parse(u) : null; }
export function setStoredUser(u: any | null)   { u ? localStorage.setItem('user_data', JSON.stringify(u)) : localStorage.removeItem('user_data'); }

function authHeaders(): HeadersInit {
  const token = getAuthToken();
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
}

let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

export async function refreshTokenApi(): Promise<string> {
  const refresh = getRefreshToken();
  if (!refresh) {
    setAuthToken(null, null);
    setStoredUser(null);
    throw new Error('No refresh token available');
  }

  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${BASE}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${refresh}` },
        body: JSON.stringify({ refresh_token: refresh })
      });

      if (!res.ok) {
        setAuthToken(null, null);
        setStoredUser(null);
        throw new Error('Refresh token expired or invalid');
      }

      const data: AuthResponse = await res.json();
      setAuthToken(data.access_token, data.refresh_token);
      return data.access_token;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

async function handleResponse<T>(res: Response, retryFn?: () => Promise<Response>): Promise<T> {
  if (res.status === 401 && retryFn) {
    try {
      await refreshTokenApi();
      const retryRes = await retryFn();
      if (!retryRes.ok) {
        const err = await retryRes.json().catch(() => ({ detail: `HTTP ${retryRes.status}` }));
        throw new Error(err.detail || `Request failed (${retryRes.status})`);
      }
      return retryRes.json();
    } catch {
      setAuthToken(null, null);
      setStoredUser(null);
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

/* ── Auth ── */
export async function loginApi(username: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/api/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
  const data = await handleResponse<AuthResponse>(res);
  setAuthToken(data.access_token, data.refresh_token);
  setStoredUser(data.user);
  return data;
}

export async function registerApi(username: string, email: string, password: string, role: string, full_name: string): Promise<AuthResponse> {
  const res = await fetch(`${BASE}/api/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, email, password, role, full_name }) });
  const data = await handleResponse<AuthResponse>(res);
  setAuthToken(data.access_token, data.refresh_token);
  setStoredUser(data.user);
  return data;
}

/* ── Health ── */
export async function getHealthApi(): Promise<{ status: string; service: string; version: string }> {
  const res = await fetch(`${BASE}/api/health`);
  return handleResponse(res);
}

/* ── Doctor endpoints ── */
export async function getDashboardApi(): Promise<DashboardData> {
  const res = await fetch(`${BASE}/api/doctor/dashboard`, { headers: authHeaders() });
  return handleResponse(res);
}

export async function getReviewQueueApi(statusFilter?: string): Promise<ReviewQueueItem[]> {
  const qs = statusFilter && statusFilter !== 'ALL' ? `?status_filter=${statusFilter}` : '';
  const res = await fetch(`${BASE}/api/doctor/review-queue${qs}`, { headers: authHeaders() });
  return handleResponse(res);
}

export async function postReviewActionApi(reviewId: string, action: string, reviewer: string, newValue?: string) {
  const res = await fetch(`${BASE}/api/doctor/review/${reviewId}/action`, {
    method: 'POST', headers: authHeaders(),
    body: JSON.stringify({ action, reviewer, new_value: newValue ?? null })
  });
  return handleResponse(res);
}

export async function batchApproveAllApi() {
  const res = await fetch(`${BASE}/api/doctor/review-queue/approve-all`, { method: 'POST', headers: authHeaders(), body: '{}' });
  return handleResponse(res);
}

export async function getPatientHistoryApi(search?: string): Promise<PatientHistoryRecord[]> {
  const qs = search ? `?search=${encodeURIComponent(search)}` : '';
  const res = await fetch(`${BASE}/api/doctor/patient-history${qs}`, { headers: authHeaders() });
  return handleResponse(res);
}

export async function getSessionJsonApi(sessionId: string) {
  const res = await fetch(`${BASE}/api/doctor/export/json/${sessionId}`, { headers: authHeaders() });
  return handleResponse(res);
}

export async function downloadPdfApi(sessionId: string): Promise<Blob> {
  const res = await fetch(`${BASE}/api/doctor/export/pdf/${sessionId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error('PDF export failed');
  return res.blob();
}

/* ── Extraction ── */
export async function extractClinicalTextApi(content: string): Promise<ExtractionResponse> {
  const res = await fetch(`${BASE}/api/extract`, { method: 'POST', headers: authHeaders(), body: JSON.stringify({ content }) });
  return handleResponse(res);
}

/* ── Patient endpoints ── */
export async function submitClinicalNoteApi(clinical_note: string): Promise<ExtractionResponse> {
  const res = await fetch(`${BASE}/api/patient/submit-note`, { method: 'POST', headers: authHeaders(), body: JSON.stringify({ clinical_note }) });
  return handleResponse(res);
}

export async function getMyHistoryApi() {
  const res = await fetch(`${BASE}/api/patient/history`, { headers: authHeaders() });
  return handleResponse(res);
}

export async function downloadPatientPdfApi(sessionId: string): Promise<Blob> {
  const res = await fetch(`${BASE}/api/patient/download-pdf/${sessionId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error('PDF download failed');
  return res.blob();
}

