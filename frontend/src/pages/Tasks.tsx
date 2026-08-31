import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Task } from '../types'

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
  const [error, setError] = useState<string | null>(null)
  const [advancing, setAdvancing] = useState<number | null>(null)

  const load = () =>
    api.tasks
      .list()
      .then(setItems)
      .catch((e) => setError(e.message))

  useEffect(() => {
    load()
  }, [])

  const advance = async (companyId: number) => {
    setAdvancing(companyId)
    setError(null)
    try {
      await api.execution.advance(companyId)
      await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setAdvancing(null)
    }
  }

  const companyIds = [...new Set(items.map((t) => t.company_id))]

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Tasks</h2>
          <p className="text-sm text-muted">Sequential pipeline board</p>
        </div>
        {companyIds.length > 0 && (
          <button
            type="button"
            disabled={advancing !== null}
            onClick={() => advance(companyIds[0])}
            className="min-h-[44px] rounded-lg bg-accent px-4 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50"
          >
            {advancing !== null ? 'Advancing…' : 'Advance next step'}
          </button>
        )}
      </div>
      {error && <p className="text-sm text-danger">{error}</p>}
      <div className="rounded-xl border border-border bg-surface-2 divide-y divide-border">
        {items.map((t) => (
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
        {items.length === 0 && !error && (
          <p className="px-4 py-6 text-sm text-muted text-center">No tasks</p>
        )}
      </div>
    </div>
  )
}
