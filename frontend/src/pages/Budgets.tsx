import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Company, Agent } from '../types'

export default function Budgets() {
  const [companies, setCompanies] = useState<Company[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    setError(null)
    Promise.all([api.companies.list(), api.agents.list()])
      .then(([c, a]) => {
        setCompanies(c)
        setAgents(a)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Budgets</h2>
          <p className="text-sm text-muted">Hard monthly caps — exceed = auto-pause</p>
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
        <>
          <section className="space-y-2">
            <h3 className="text-xs uppercase tracking-wide text-muted">Companies</h3>
            {companies.map((c) => {
              const pct =
                c.monthly_budget > 0
                  ? Math.min(100, (c.current_month_spend / c.monthly_budget) * 100)
                  : 0
              return (
                <div key={c.id} className="rounded-xl border border-border bg-surface-2 p-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium">{c.name}</span>
                    <span className="tabular-nums text-muted">
                      ${c.current_month_spend.toFixed(2)} / ${c.monthly_budget.toFixed(2)}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-surface-3 overflow-hidden">
                    <div
                      className={`h-full ${pct > 90 ? 'bg-danger' : pct > 70 ? 'bg-warning' : 'bg-accent'}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </section>

          <section className="space-y-2">
            <h3 className="text-xs uppercase tracking-wide text-muted">Agents</h3>
            <div className="rounded-xl border border-border bg-surface-2 divide-y divide-border">
              {agents.map((a) => {
                const pct =
                  a.monthly_budget > 0
                    ? Math.min(100, (a.current_month_spend / a.monthly_budget) * 100)
                    : 0
                return (
                  <div key={a.id} className="px-4 py-3">
                    <div className="flex justify-between text-sm mb-1.5">
                      <span>
                        {a.name}{' '}
                        <span className="text-muted text-xs">({a.role})</span>
                      </span>
                      <span className="tabular-nums text-xs text-muted">
                        ${a.current_month_spend.toFixed(2)} / ${a.monthly_budget.toFixed(0)}
                      </span>
                    </div>
                    <div className="h-1.5 rounded-full bg-surface-3 overflow-hidden">
                      <div
                        className={`h-full ${
                          a.status === 'paused_budget' || pct > 90
                            ? 'bg-danger'
                            : pct > 70
                              ? 'bg-warning'
                              : 'bg-accent'
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        </>
      )}
    </div>
  )
}
