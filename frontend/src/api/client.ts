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
    const detail = body.detail
    const msg =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).join(', ')
          : res.statusText || `HTTP ${res.status}`
    throw new Error(msg)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export type CompanyCreate = {
  name: string
  mission?: string | null
  monthly_budget?: number
}

export type CompanyUpdate = {
  name?: string
  mission?: string | null
  monthly_budget?: number
}

export type AgentCreate = {
  company_id: number
  name: string
  role: string
  system_prompt?: string | null
  description?: string | null
  provider?: string
  model?: string
  monthly_budget?: number
  parent_id?: number | null
}

export type AgentUpdate = {
  name?: string
  role?: string
  system_prompt?: string | null
  description?: string | null
  provider?: string
  model?: string
  monthly_budget?: number
  parent_id?: number | null
  status?: string
}

export const api = {
  companies: {
    list: () => request<import('../types').Company[]>('/api/companies/'),
    get: (id: number) => request<import('../types').Company>(`/api/companies/${id}`),
    create: (body: CompanyCreate) =>
      request<import('../types').Company>('/api/companies/', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    update: (id: number, body: CompanyUpdate) =>
      request<import('../types').Company>(`/api/companies/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      }),
    remove: (id: number) =>
      request<void>(`/api/companies/${id}`, { method: 'DELETE' }),
  },
  agents: {
    list: (companyId?: number) =>
      request<import('../types').Agent[]>(
        companyId ? `/api/agents/?company_id=${companyId}` : '/api/agents/'
      ),
    create: (body: AgentCreate) =>
      request<import('../types').Agent>('/api/agents/', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    update: (id: number, body: AgentUpdate) =>
      request<import('../types').Agent>(`/api/agents/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      }),
    remove: (id: number) =>
      request<void>(`/api/agents/${id}`, { method: 'DELETE' }),
    pause: (id: number) =>
      request<import('../types').Agent>(`/api/agents/${id}/pause`, { method: 'POST' }),
    resume: (id: number) =>
      request<import('../types').Agent>(`/api/agents/${id}/resume`, { method: 'POST' }),
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
