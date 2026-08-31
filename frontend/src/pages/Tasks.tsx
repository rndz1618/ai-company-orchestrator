import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Task, Company } from '../types'

const statusStyle: Record<string, string> = {
  pending: 'text-muted',
  ready: 'text-accent',
  running: 'text-accent',
  waiting_approval: 'text-warning',
  completed: 'text-success',
  failed: 'text-danger',
  cancelled: 'text-muted',
}

export default function Tasks() {
  const [items, setItems] = useState<Task[]>([])
  const [companies, setCompanies] = useState<Company[]>([])
  const [selectedCompany, setSelectedCompany] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [advancing, setAdvancing] = useState(false)

  const load = () => {
    setLoading(true)
    setError(null)
    Promise.all([api.tasks.list(), api.companies.list()])
      .then(([t, c]) => {
        setItems(t)
        setCompanies(c)
        if (selectedCompany === null && c.length > 0) {
          setSelectedCompany(c[0].id)
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const advance = async () => {
    if (selectedCompany == null) return
    setAdvancing(true)
    setError(null)
    try {
      await api.execution.advance(selectedCompany)
      await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setAdvancing(false)
    }
  }

  const filtered =
    selectedCompany == null ? items : items.filter((t) => t.company_id === selectedCompany)

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Tasks</h2>
          <p className="text-sm text-muted">Sequential pipeline board</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {companies.length > 0 && (
            <select
              value={selectedCompany ?? ''}
              onChange={(e) => setSelectedCompany(Number(e.target.value))}
              className="min-h-[44px] rounded-lg border border-border bg-surface-2 px-3 text-sm"
            >
              {companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}
          <button
            type="button"
            disabled={advancing || selectedCompany == null}
            onClick={advance}
            className="min-h-[44px] rounded-lg bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50"
          >
            {advancing ? 'Advancing…' : 'Advance next step'}
          </button>
          <button
            type="button"
            onClick={load}
            className="min-h-[44px] rounded-lg border border-border px-3 text-sm text-muted hover:bg-surface-3"
          >
            Refresh
          </button>
        </div>
      </div>
      {error && <p className="text-sm text-danger">{error}</p>}
      {loading && <p className="text-sm text-muted">Loading…</p>}
      {!loading && (
        <div className="rounded-xl border border-border bg-surface-2 divide-y divide-border">
          {filtered.map((t) => (
            <div key={t.id} className="px-4 py-3 space-y-1">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium">{t.title}</p>
                <span className={`text-xs font-medium shrink-0 ${statusStyle[t.status]}`}>
                  {t.status.replace(/_/g, ' ')}
                </span>
              </div>
              <p className="text-xs text-muted">
                #{t.id}
                {t.stage_index != null ? ` · stage ${t.stage_index}` : ''}
                {t.requires_human_approval ? ' · HITL' : ''}
                {t.actual_cost != null ? ` · $${t.actual_cost.toFixed(4)}` : ''}
              </p>
              {t.error_message && (
                <p className="text-xs text-danger line-clamp-2">{t.error_message}</p>
              )}
            </div>
          ))}
          {filtered.length === 0 && (
            <p className="px-4 py-6 text-sm text-muted text-center">No tasks</p>
          )}
        </div>
      )}
    </div>
  )
}
