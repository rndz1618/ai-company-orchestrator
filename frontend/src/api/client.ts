const API_BASE = import.meta.env.VITE_API_URL || ''

function headers(): HeadersInit {
  const h: HeadersInit = { 'Content-Type': 'application/json' }
  const key = localStorage.getItem('orchestrator_api_key')
  if (key) h['X-API-Key'] = key
  return h
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...headers(), ...init?.headers },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || res.statusText || `HTTP ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  companies: {
    list: () => request<import('../types').Company[]>('/api/companies/'),
    get: (id: number) => request<import('../types').Company>(`/api/companies/${id}`),
  },
  agents: {
    list: (companyId?: number) =>
      request<import('../types').Agent[]>(
        companyId ? `/api/agents/?company_id=${companyId}` : '/api/agents/'
      ),
  },
  tasks: {
    list: (companyId?: number) =>
      request<import('../types').Task[]>(
        companyId ? `/api/tasks/?company_id=${companyId}` : '/api/tasks/'
      ),
  },
  budgets: {
    companySummary: (id: number) =>
      request<{ monthly_budget: number; current_month_spend: number; remaining: number }>(
        `/api/budgets/company/${id}`
      ),
  },
  execution: {
    advance: (companyId: number) =>
      request<import('../types').Task[]>(`/api/execution/companies/${companyId}/advance`, {
        method: 'POST',
      }),
  },
  health: () => request<{ status: string; app?: string; version?: string }>('/health'),
}
