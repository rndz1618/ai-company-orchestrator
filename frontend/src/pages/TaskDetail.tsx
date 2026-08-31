import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Task } from '../types'
import { ArrowLeft, CheckCircle2, XCircle, Play } from 'lucide-react'

const statusStyle: Record<string, string> = {
  pending: 'bg-surface-3 text-muted',
  ready: 'bg-accent/15 text-accent',
  running: 'bg-accent/15 text-accent',
  waiting_approval: 'bg-warning/15 text-warning',
  completed: 'bg-success/15 text-success',
  failed: 'bg-danger/15 text-danger',
  cancelled: 'bg-surface-3 text-muted',
}

export default function TaskDetail() {
  const { taskId } = useParams()
  const id = Number(taskId)
  const [task, setTask] = useState<Task | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [approvedBy, setApprovedBy] = useState('board')
  const [canRun, setCanRun] = useState<{ can_run: boolean; reason?: string } | null>(null)

  const load = async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const t = await api.tasks.get(id)
      setTask(t)
      try {
        const cr = await api.execution.canRun(id)
        setCanRun(cr)
      } catch {
        setCanRun(null)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const approve = async () => {
    if (!task) return
    setBusy(true)
    setError(null)
    try {
      const t = await api.tasks.approve(task.id, approvedBy.trim() || 'board')
      setTask(t)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const cancel = async () => {
    if (!task) return
    if (!confirm('Cancel this task?')) return
    setBusy(true)
    setError(null)
    try {
      const t = await api.tasks.cancel(task.id)
      setTask(t)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const run = async () => {
    if (!task) return
    setBusy(true)
    setError(null)
    try {
      const res = await api.execution.runTask(task.id)
      const t = (res as { task?: Task }).task || (res as unknown as Task)
      if (t && 'id' in t) setTask(t)
      else await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <p className="text-sm text-muted">Loading task…</p>
  if (!task) {
    return (
      <div className="space-y-3">
        <Link to="/tasks" className="text-sm text-accent inline-flex items-center gap-1">
          <ArrowLeft size={16} /> Back to tasks
        </Link>
        <p className="text-sm text-danger">{error || 'Task not found'}</p>
      </div>
    )
  }

  const waiting = task.status === 'waiting_approval'
  const finished = ['completed', 'cancelled', 'failed'].includes(task.status)

  return (
    <div className="space-y-5 max-w-2xl">
      <div className="flex items-start justify-between gap-3">
        <div>
          <Link to="/tasks" className="text-xs text-muted inline-flex items-center gap-1 hover:text-text">
            <ArrowLeft size={14} /> Tasks
          </Link>
          <h2 className="text-xl font-semibold mt-1">{task.title}</h2>
          <p className="text-xs text-muted mt-0.5">#{task.id} · company {task.company_id}</p>
        </div>
        <span
          className={`text-[11px] font-medium px-2.5 py-1 rounded-full shrink-0 ${
            statusStyle[task.status] || statusStyle.pending
          }`}
        >
          {task.status.replace(/_/g, ' ')}
        </span>
      </div>

      {error && (
        <div className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </div>
      )}

      {waiting && (
        <section className="rounded-xl border border-warning/40 bg-warning/10 p-4 space-y-3">
          <div className="flex items-start gap-2">
            <CheckCircle2 size={18} className="text-warning shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-warning">Human approval required</h3>
              <p className="text-xs text-muted mt-0.5">
                Board must approve before this stage is marked complete and the pipeline can advance.
              </p>
            </div>
          </div>
          <label className="block space-y-1">
            <span className="text-xs text-muted">Approved by</span>
            <input
              value={approvedBy}
              onChange={(e) => setApprovedBy(e.target.value)}
              className="w-full min-h-[44px] rounded-lg border border-border bg-surface px-3 text-sm"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={approve}
              className="min-h-[44px] inline-flex items-center gap-1.5 rounded-lg bg-success px-4 text-sm font-medium text-white disabled:opacity-50"
            >
              <CheckCircle2 size={16} />
              {busy ? 'Approving…' : 'Approve'}
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={cancel}
              className="min-h-[44px] inline-flex items-center gap-1.5 rounded-lg border border-border px-4 text-sm disabled:opacity-50"
            >
              <XCircle size={16} /> Reject / Cancel
            </button>
          </div>
        </section>
      )}

      {!waiting && !finished && (
        <div className="flex flex-wrap gap-2">
          {canRun?.can_run && (
            <button
              type="button"
              disabled={busy}
              onClick={run}
              className="min-h-[44px] inline-flex items-center gap-1.5 rounded-lg bg-accent px-4 text-sm font-medium text-white disabled:opacity-50"
            >
              <Play size={16} />
              {busy ? 'Running…' : 'Run task'}
            </button>
          )}
          {canRun && !canRun.can_run && (
            <p className="text-xs text-muted self-center">
              Cannot run: {canRun.reason || 'not ready'}
            </p>
          )}
          <button
            type="button"
            disabled={busy}
            onClick={cancel}
            className="min-h-[44px] rounded-lg border border-border px-4 text-sm disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={load}
            className="min-h-[44px] rounded-lg border border-border px-3 text-sm text-muted"
          >
            Refresh
          </button>
        </div>
      )}

      <section className="rounded-xl border border-border bg-surface-2 divide-y divide-border text-sm">
        <Row label="Description" value={task.description || '—'} />
        <Row label="Agent ID" value={task.agent_id != null ? String(task.agent_id) : '—'} />
        <Row
          label="Depends on"
          value={task.depends_on_id != null ? `#${task.depends_on_id}` : '—'}
        />
        <Row label="HITL required" value={task.requires_human_approval ? 'Yes' : 'No'} />
        <Row
          label="Cost"
          value={
            task.actual_cost != null
              ? `$${task.actual_cost.toFixed(4)}${
                  task.estimated_cost != null ? ` (est $${task.estimated_cost.toFixed(4)})` : ''
                }`
              : task.estimated_cost != null
                ? `est $${task.estimated_cost.toFixed(4)}`
                : '—'
          }
        />
        <Row
          label="Tokens"
          value={
            task.tokens_input != null || task.tokens_output != null
              ? `in ${task.tokens_input ?? 0} / out ${task.tokens_output ?? 0}`
              : '—'
          }
        />
        <Row
          label="Approved"
          value={
            task.approved_by
              ? `${task.approved_by}${task.approved_at ? ` · ${new Date(task.approved_at).toLocaleString()}` : ''}`
              : '—'
          }
        />
        <Row label="Created" value={new Date(task.created_at).toLocaleString()} />
        <Row
          label="Started"
          value={task.started_at ? new Date(task.started_at).toLocaleString() : '—'}
        />
        <Row
          label="Completed"
          value={task.completed_at ? new Date(task.completed_at).toLocaleString() : '—'}
        />
      </section>

      {task.error_message && (
        <section className="rounded-xl border border-danger/40 bg-danger/10 p-4">
          <h3 className="text-xs uppercase tracking-wide text-danger mb-1">Error</h3>
          <pre className="text-xs whitespace-pre-wrap text-danger/90">{task.error_message}</pre>
        </section>
      )}

      {task.result && (
        <section className="rounded-xl border border-border bg-surface-2 p-4">
          <h3 className="text-xs uppercase tracking-wide text-muted mb-2">Result</h3>
          <pre className="text-xs whitespace-pre-wrap text-text/90 max-h-96 overflow-y-auto">
            {task.result}
          </pre>
        </section>
      )}
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3 px-4 py-2.5">
      <span className="text-xs text-muted w-28 shrink-0 pt-0.5">{label}</span>
      <span className="text-sm break-words min-w-0">{value}</span>
    </div>
  )
}
