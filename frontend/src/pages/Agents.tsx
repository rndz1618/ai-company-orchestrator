import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Agent } from '../types'

const statusStyle: Record<string, string> = {
  active: 'bg-success/15 text-success',
  paused_budget: 'bg-danger/15 text-danger',
  paused_manual: 'bg-warning/15 text-warning',
  disabled: 'bg-surface-3 text-muted',
}

export default function Agents() {
  const [items, setItems] = useState<Agent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    setError(null)
    api.agents
      .list()
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Agents</h2>
          <p className="text-sm text-muted">Roles, providers, and spend caps</p>
        </div>
        <button
          type="button"
          onClick={load}
          className="min-h-[44px] rounded-lg border border-border px-3 text-sm text-muted hover:bg-surface-3"
        >
          Refresh
        </button>
      </div>
      {error && <p className="text-sm text-danger">{error}</p>}
      {loading && <p className="text-sm text-muted">Loading…</p>}
      {!loading && (
        <div className="rounded-xl border border-border bg-surface-2 divide-y divide-border overflow-hidden">
          {items.map((a) => (
            <div
              key={a.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-4 py-3"
            >
              <div className="min-w-0">
                <p className="font-medium text-sm">{a.name}</p>
                <p className="text-xs text-muted">
                  {a.role} · {a.provider}/{a.model}
                </p>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-xs tabular-nums text-muted">
                  ${a.current_month_spend.toFixed(2)} / ${a.monthly_budget.toFixed(0)}
                </span>
                <span
                  className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                    statusStyle[a.status] || statusStyle.disabled
                  }`}
                >
                  {a.status.replace(/_/g, ' ')}
                </span>
              </div>
            </div>
          ))}
          {items.length === 0 && !error && (
            <p className="px-4 py-6 text-sm text-muted text-center">No agents hired yet</p>
          )}
        </div>
      )}
    </div>
  )
}
