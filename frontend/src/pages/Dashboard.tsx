import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Company, Agent, Task } from '../types'
import { Building2, Bot, ListTodo, Wallet } from 'lucide-react'

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
}: {
  label: string
  value: string | number
  sub?: string
  icon: typeof Building2
}) {
  return (
    <div className="rounded-xl border border-border bg-surface-2 p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs text-muted uppercase tracking-wide">{label}</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
          {sub && <p className="mt-1 text-xs text-muted">{sub}</p>}
        </div>
        <div className="rounded-lg bg-surface-3 p-2 text-accent">
          <Icon size={18} />
        </div>
      </div>
    </div>
  )
}

function statusColor(status: string) {
  switch (status) {
    case 'active':
    case 'completed':
      return 'text-success'
    case 'running':
    case 'ready':
      return 'text-accent'
    case 'waiting_approval':
    case 'paused_manual':
      return 'text-warning'
    case 'failed':
    case 'paused_budget':
    case 'disabled':
      return 'text-danger'
    default:
      return 'text-muted'
  }
}

export default function Dashboard() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.companies.list(), api.agents.list(), api.tasks.list()])
      .then(([c, a, t]) => {
        setCompanies(c)
        setAgents(a)
        setTasks(t)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const totalSpend = companies.reduce((s, c) => s + (c.current_month_spend || 0), 0)
  const totalBudget = companies.reduce((s, c) => s + (c.monthly_budget || 0), 0)
  const activeAgents = agents.filter((a) => a.status === 'active').length
  const openTasks = tasks.filter((t) =>
    ['pending', 'ready', 'running', 'waiting_approval'].includes(t.status)
  ).length

  if (loading) {
    return <p className="text-muted text-sm">Loading overview…</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Overview</h2>
        <p className="text-sm text-muted mt-0.5">Company health at a glance</p>
      </div>

      {error && (
        <div className="rounded-lg border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
          API error: {error}. Is the backend running on :8000?
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Companies" value={companies.length} icon={Building2} />
        <StatCard
          label="Active agents"
          value={activeAgents}
          sub={`${agents.length} total`}
          icon={Bot}
        />
        <StatCard label="Open tasks" value={openTasks} icon={ListTodo} />
        <StatCard
          label="Spend / Budget"
          value={`$${totalSpend.toFixed(0)}`}
          sub={`of $${totalBudget.toFixed(0)}`}
          icon={Wallet}
        />
      </div>

      <section className="space-y-3">
        <h3 className="text-sm font-medium text-muted uppercase tracking-wide">Recent tasks</h3>
        <div className="rounded-xl border border-border bg-surface-2 divide-y divide-border">
          {tasks.slice(0, 8).map((t) => (
            <div key={t.id} className="flex items-center justify-between gap-3 px-4 py-3">
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{t.title}</p>
                <p className="text-xs text-muted">#{t.id}</p>
              </div>
              <span className={`text-xs font-medium shrink-0 ${statusColor(t.status)}`}>
                {t.status.replace(/_/g, ' ')}
              </span>
            </div>
          ))}
          {tasks.length === 0 && (
            <p className="px-4 py-6 text-sm text-muted text-center">No tasks yet</p>
          )}
        </div>
      </section>
    </div>
  )
}
