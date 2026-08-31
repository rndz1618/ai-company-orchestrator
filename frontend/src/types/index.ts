export type AgentStatus = 'active' | 'paused_budget' | 'paused_manual' | 'disabled'
export type TaskStatus =
  | 'pending'
  | 'ready'
  | 'running'
  | 'waiting_approval'
  | 'completed'
  | 'failed'
  | 'cancelled'

export interface Company {
  id: number
  name: string
  mission?: string | null
  monthly_budget: number
  current_month_spend: number
  budget_month: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Agent {
  id: number
  company_id: number
  name: string
  role: string
  system_prompt?: string | null
  description?: string | null
  provider: string
  model: string
  monthly_budget: number
  current_month_spend: number
  status: AgentStatus
  parent_id?: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Task {
  id: number
  company_id: number
  agent_id?: number | null
  title: string
  description?: string | null
  status: TaskStatus
  depends_on_id?: number | null
  requires_human_approval: boolean
  approved_by?: string | null
  approved_at?: string | null
  result?: string | null
  error_message?: string | null
  estimated_cost?: number | null
  actual_cost?: number | null
  tokens_input?: number | null
  tokens_output?: number | null
  stage_index?: number | null
  workflow_template_id?: number | null
  is_active?: boolean
  created_at: string
  started_at?: string | null
  completed_at?: string | null
}
