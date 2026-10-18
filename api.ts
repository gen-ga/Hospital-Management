const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export interface ApiUser { user_id: number; email: string; role: 'ADMIN' | 'DOCTOR' | 'PATIENT'; display_name: string | null; is_active: boolean; }
export interface ScheduleSlot { time: string; remaining: number; available: boolean; }
export class ApiError extends Error {
  alternatives: string[];
  constructor(message: string, alternatives: string[] = []) {
    super(message);
    this.alternatives = alternatives;
  }
}

function toError(body: unknown, status: number) {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === 'string') return new ApiError(detail);
  if (Array.isArray(detail)) return new ApiError(detail.map((item) => (item as { msg?: string }).msg || String(item)).join('; '));
  if (detail && typeof detail === 'object') {
    const payload = detail as { message?: string; alternatives?: string[] };
    return new ApiError(payload.message || `Request failed (${status})`, payload.alternatives || []);
  }
  return new ApiError(`Request failed (${status})`);
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: 'include',
    headers: { ...(init.body ? { 'Content-Type': 'application/json' } : {}), ...init.headers },
  });
  if (response.status === 204) return undefined as T;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw toError(body, response.status);
  return body as T;
}

export const apiClient = {
  me: () => api<ApiUser>('/api/auth/me'),
  login: (email: string, password: string) => api<ApiUser>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  logout: () => api<void>('/api/auth/logout', { method: 'POST' }),
  register: (payload: Record<string, unknown>) => api<ApiUser>('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  createDoctorAccount: (payload: Record<string, unknown>) => api<Record<string, unknown>>('/api/auth/admin/doctors', { method: 'POST', body: JSON.stringify(payload) }),
  list: <T,>(resource: string) => api<T[]>(`/api/${resource}`),
  scheduleSlots: (departmentId: number, date: string) =>
    api<{ department_id: number; date: string; slots: ScheduleSlot[] }>(`/api/schedule/slots?department_id=${departmentId}&date=${date}`),
  create: <T,>(resource: string, payload: Record<string, unknown>) => api<T>(`/api/${resource}`, { method: 'POST', body: JSON.stringify(payload) }),
  update: <T,>(resource: string, id: number | string, payload: Record<string, unknown>) => api<T>(`/api/${resource}/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  remove: (resource: string, id: number | string) => api<void>(`/api/${resource}/${id}`, { method: 'DELETE' }),
  uploadReport: async (file: File, metadata: { patient_id: number; appointment_id?: number; document_name: string; document_type: string; report_date: string }) => {
    const query = new URLSearchParams({ patient_id: String(metadata.patient_id), document_name: metadata.document_name, document_type: metadata.document_type, report_date: metadata.report_date });
    if (metadata.appointment_id) query.set('appointment_id', String(metadata.appointment_id));
    return api<Record<string, unknown>>(`/api/reports/upload?${query.toString()}`, { method: 'POST', headers: { 'Content-Type': file.type }, body: file });
  },
  downloadReport: async (id: string, name: string) => {
    const response = await fetch(`${API_BASE}/api/reports/${id}/download`, { credentials: 'include' });
    if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || `Download failed (${response.status})`);
    const objectUrl = URL.createObjectURL(await response.blob()); const anchor = document.createElement('a');
    anchor.href = objectUrl; anchor.download = name; anchor.click(); URL.revokeObjectURL(objectUrl);
  },
};
