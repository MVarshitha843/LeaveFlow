import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('leaveflow_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('leaveflow_token');
      localStorage.removeItem('leaveflow_user');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (data: any) => api.post('/auth/login', data),
  register: (data: any) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  getDemoAccounts: () => api.get('/auth/demo-accounts'),
};

export const employeeApi = {
  list: (params?: any) => api.get('/employees', { params }),
  get: (id: string) => api.get(`/employees/${id}`),
  departments: () => api.get('/departments'),
  costCenters: (department_id?: string) => api.get('/cost-centers', { params: { department_id } }),
};

export const leaveApi = {
  policies: () => api.get('/leave/policies'),
  balances: (employee_id?: string) => api.get('/leave/balances', { params: { employee_id } }),
  holidays: (year?: number) => api.get('/leave/holidays', { params: { year } }),
  dryRun: (data: any) => api.post('/leave/dry-run', data),
  submit: (data: any) => api.post('/leave/requests', data),
  list: (params?: any) => api.get('/leave/requests', { params }),
  get: (id: string) => api.get(`/leave/requests/${id}`),
  cancel: (id: string) => api.post(`/leave/requests/${id}/cancel`),
};

export const expenseApi = {
  policies: () => api.get('/expenses/policies'),
  uploadReceipt: (formData: FormData) => api.post('/expenses/upload-receipt', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  dryRun: (data: any) => api.post('/expenses/dry-run', data),
  submit: (data: any) => api.post('/expenses/claims', data),
  list: (params?: any) => api.get('/expenses/claims', { params }),
  get: (id: string) => api.get(`/expenses/claims/${id}`),
  cancel: (id: string) => api.post(`/expenses/claims/${id}/cancel`),
};

export const approvalApi = {
  pending: () => api.get('/approvals/pending'),
  getSteps: (requestId: string) => api.get(`/approvals/request/${requestId}`),
  approve: (stepId: string, comments?: string) => api.post(`/approvals/${stepId}/approve`, { action: 'APPROVE', comments }),
  reject: (stepId: string, comments: string) => api.post(`/approvals/${stepId}/reject`, { action: 'REJECT', comments }),
  requestInfo: (stepId: string, comments: string) => api.post(`/approvals/${stepId}/request-information`, { action: 'REQUEST_INFO', comments }),
  reimburse: (claimId: string) => api.post(`/approvals/reimburse/${claimId}`),
};

export const decisionApi = {
  getDetails: (requestId: string) => api.get(`/decision/${requestId}`),
  getGraph: (requestId: string) => api.get(`/decision/${requestId}/graph`),
};

export const reservationApi = {
  list: (params?: any) => api.get('/reservations', { params }),
  get: (id: number) => api.get(`/reservations/${id}`),
};

export const anomalyApi = {
  list: (params?: any) => api.get('/anomalies', { params }),
  scan: () => api.post('/anomalies/scan'),
  review: (id: number, status: string, notes?: string) => api.post(`/anomalies/${id}/review`, { status, notes }),
};

export const auditApi = {
  events: (params?: any) => api.get('/audit/events', { params }),
  requestTrail: (requestId: string) => api.get(`/audit/request/${requestId}`),
  verify: () => api.get('/audit/verify'),
};

export const analyticsApi = {
  overview: () => api.get('/analytics/overview'),
};

export const notificationApi = {
  list: () => api.get('/notifications'),
  unreadCount: () => api.get('/notifications/unread-count'),
  markRead: (id: number) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
};

export const policyApi = {
  getAll: () => api.get('/policies'),
  updateLeave: (id: string, data: any) => api.post(`/policies/leave/${id}`, null, { params: data }),
  updateExpense: (id: string, data: any) => api.post(`/policies/expense/${id}`, null, { params: data }),
};

export default api;
