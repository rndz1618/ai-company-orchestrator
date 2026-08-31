import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Company } from '../types'

export default function Companies() {
  const [items, setItems] = useState<Company[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.companies
      .list()
      .then(setItems)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold">Companies</h2>
        <p className="text-sm text-muted">Virtual companies you direct as Board</p>
      </div>
      {error && <p className="text-sm text-danger">{error}</p>}
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((c) => {
          const pct =
            c.monthly_budget > 0
              ? Math.min(100, (c.current_month_spend / c.monthly_budget) * 100)
              : 0
          return (
            <article
              key={c.id}
              className="rounded-xl border border-border bg-surface-2 p-4 space-y-3"
            >
              <div>
                <h3 className="font-medium">{c.name}</h3>
                {c.mission && (
                  <p className="text-xs text-muted mt-1 line-clamp-2">{c.mission}</p>
                )}
              </div>
              <div>
                <div className="flex justify-between text-xs text-muted mb-1">
                  <span>Budget</span>
                  <span>
                    ${c.current_month_spend.toFixed(2)} / ${c.monthly_budget.toFixed(2)}
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-surface-3 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      pct > 90 ? 'bg-danger' : pct > 70 ? 'bg-warning' : 'bg-accent'
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            </article>
          )
        })}
        {items.length === 0 && !error && (
          <p className="text-sm text-muted col-span-full">No companies yet. Create via API.</p>
        )}
      </div>
    </div>
  )
}
