import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Company, WorkflowStage, WorkflowTemplate } from '../types'
import Modal from '../components/Modal'
import { Plus, Trash2, Play, GitBranch } from 'lucide-react'

const emptyStage = (): WorkflowStage => ({
  name: '',
  role: '',
  requires_human_approval: false,
  description: '',
})

export default function Workflows() {
  const [items, setItems] = useState<WorkflowTemplate[]>([])
  const [companies, setCompanies] = useState<Company[]>([])
  const [filterCompany, setFilterCompany] = useState<number | 'all'>('all')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [startingId, setStartingId] = useState<number | null>(null)
  const [prefix, setPrefix] = useState('')

  const [formCompany, setFormCompany] = useState(0)
  const [formName, setFormName] = useState('')
  const [formDesc, setFormDesc] = useState('')
  const [stages, setStages] = useState<WorkflowStage[]>([emptyStage(), emptyStage()])

  const load = () => {
    setLoading(true)
    setError(null)
    setSuccess(null)
    const cid = filterCompany === 'all' ? undefined : filterCompany
    Promise.all([api.workflows.list(cid), api.companies.list()])
      .then(([w, c]) => {
        setItems(w)
        setCompanies(c)
        if (!formCompany && c[0]) setFormCompany(c[0].id)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterCompany])

  const openCreate = () => {
    setFormName('')
    setFormDesc('')
    setStages([emptyStage(), emptyStage()])
    setFormCompany(filterCompany !== 'all' ? filterCompany : companies[0]?.id ?? 0)
    setModalOpen(true)
  }

  const updateStage = (i: number, patch: Partial<WorkflowStage>) => {
    setStages((prev) => prev.map((s, idx) => (idx === i ? { ...s, ...patch } : s)))
  }

  const addStage = () => setStages((prev) => [...prev, emptyStage()])
  const removeStage = (i: number) =>
    setStages((prev) => (prev.length <= 1 ? prev : prev.filter((_, idx) => idx !== i)))

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    const clean = stages
      .map((s) => ({
        name: s.name.trim(),
        role: s.role.trim(),
        requires_human_approval: !!s.requires_human_approval,
        description: s.description?.trim() || undefined,
      }))
      .filter((s) => s.name && s.role)
    if (!formName.trim() || !formCompany || clean.length === 0) {
      setError('Name, company, and at least one stage (name + role) required')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await api.workflows.create({
        company_id: formCompany,
        name: formName.trim(),
        description: formDesc.trim() || null,
        stages: clean,
      })
      setModalOpen(false)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  const remove = async (w: WorkflowTemplate) => {
    if (!confirm(`Delete workflow "${w.name}"?`)) return
    try {
      await api.workflows.remove(w.id)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  const start = async (w: WorkflowTemplate) => {
    setStartingId(w.id)
    setError(null)
    setSuccess(null)
    try {
      const tasks = await api.workflows.start(
        w.id,
        w.company_id,
        prefix.trim() || undefined
      )
      setSuccess(
        `Started → ${tasks.length} task(s) created. Open Tasks to run / advance / approve.`
      )
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setStartingId(null)
    }
  }

  const companyName = (id: number) =>
    companies.find((c) => c.id === id)?.name || `#${id}`

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <GitBranch size={22} className="text-accent" />
            Workflows
          </h2>
          <p className="text-sm text-muted">Sequential stages · role → agent · optional HITL</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {companies.length > 0 && (
            <select
              value={filterCompany}
              onChange={(e) =>
                setFilterCompany(e.target.value === 'all' ? 'all' : Number(e.target.value))
              }
              className="min-h-[44px] rounded-lg border border-border bg-surface-2 px-3 text-sm"
            >
              <option value="all">All companies</option>
              {companies.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}
          <button type="button" onClick={load} className="min-h-[44px] rounded-lg border border-border px-3 text-sm text-muted">
            Refresh
          </button>
          <button
            type="button"
            onClick={openCreate}
            disabled={companies.length === 0}
            className="min-h-[44px] inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 text-sm font-medium text-white disabled:opacity-50"
          >
            <Plus size={16} /> New workflow
          </button>
        </div>
      </div>

      <label className="flex flex-col sm:flex-row sm:items-center gap-2 text-sm">
        <span className="text-muted shrink-0">Title prefix on start</span>
        <input
          value={prefix}
          onChange={(e) => setPrefix(e.target.value)}
          placeholder="e.g. Deep dive Q3"
          className="min-h-[44px] flex-1 rounded-lg border border-border bg-surface-2 px-3 text-sm"
        />
      </label>

      {companies.length === 0 && !loading && (
        <p className="text-sm text-warning">Create a company first.</p>
      )}
      {error && (
        <div className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>
      )}
      {success && (
        <div className="rounded-lg border border-success/40 bg-success/10 px-3 py-2 text-sm text-success flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <span>{success}</span>
          <Link to="/tasks" className="underline font-medium shrink-0">
            Go to Tasks
          </Link>
        </div>
      )}
      {loading && <p className="text-sm text-muted">Loading…</p>}

      {!loading && (
        <div className="space-y-3">
          {items.map((w) => (
            <article key={w.id} className="rounded-xl border border-border bg-surface-2 p-4 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                <div>
                  <h3 className="font-medium">{w.name}</h3>
                  <p className="text-xs text-muted">
                    #{w.id} · {companyName(w.company_id)} · {Array.isArray(w.stages) ? w.stages.length : 0} stages
                  </p>
                  {w.description && <p className="text-sm text-muted mt-1">{w.description}</p>}
                </div>
                <div className="flex gap-1 shrink-0">
                  <button
                    type="button"
                    disabled={startingId === w.id}
                    onClick={() => start(w)}
                    className="min-h-[44px] inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 text-sm font-medium text-white disabled:opacity-50"
                  >
                    <Play size={16} />
                    {startingId === w.id ? 'Starting…' : 'Start'}
                  </button>
                  <button
                    type="button"
                    aria-label="Delete workflow"
                    onClick={() => remove(w)}
                    className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg hover:bg-danger/10 text-muted hover:text-danger"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <ol className="space-y-1.5">
                {(w.stages || []).map((s, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm rounded-lg bg-surface px-3 py-2 border border-border/60"
                  >
                    <span className="text-xs text-muted tabular-nums w-5 shrink-0 pt-0.5">{i + 1}.</span>
                    <div className="min-w-0">
                      <span className="font-medium">{s.name}</span>
                      <span className="text-muted"> · role </span>
                      <code className="text-xs text-accent">{s.role}</code>
                      {s.requires_human_approval && (
                        <span className="ml-2 text-[11px] text-warning font-medium">HITL</span>
                      )}
                      {s.description && <p className="text-xs text-muted mt-0.5">{s.description}</p>}
                    </div>
                  </li>
                ))}
              </ol>
              <p className="text-xs text-muted">
                After Start →{' '}
                <Link to="/tasks" className="text-accent hover:underline">Tasks</Link>
                {' '}→ Run / Advance / Approve
              </p>
            </article>
          ))}
          {items.length === 0 && (
            <p className="text-sm text-muted text-center py-8">
              No workflows. Create one with stages matching agent roles.
            </p>
          )}
        </div>
      )}

      <Modal title="New workflow" open={modalOpen} onClose={() => setModalOpen(false)}>
        <form onSubmit={save} className="space-y-3">
          <label className="block space-y-1">
            <span className="text-xs text-muted">Company *</span>
            <select
              required
              value={formCompany || ''}
              onChange={(e) => setFormCompany(Number(e.target.value))}
              className="w-full min-h-[44px] rounded-lg border border-border bg-surface px-3 text-sm"
            >
              {companies.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </label>
          <label className="block space-y-1">
            <span className="text-xs text-muted">Name *</span>
            <input
              required
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              className="w-full min-h-[44px] rounded-lg border border-border bg-surface px-3 text-sm"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-xs text-muted">Description</span>
            <input
              value={formDesc}
              onChange={(e) => setFormDesc(e.target.value)}
              className="w-full min-h-[44px] rounded-lg border border-border bg-surface px-3 text-sm"
            />
          </label>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted">Stages (sequential)</span>
              <button type="button" onClick={addStage} className="text-xs text-accent min-h-[44px] px-2">
                + Stage
              </button>
            </div>
            {stages.map((s, i) => (
              <div key={i} className="rounded-lg border border-border bg-surface p-3 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-medium text-muted">Stage {i + 1}</span>
                  {stages.length > 1 && (
                    <button type="button" onClick={() => removeStage(i)} className="text-xs text-danger min-h-[44px]">
                      Remove
                    </button>
                  )}
                </div>
                <input
                  required
                  placeholder="Stage name"
                  value={s.name}
                  onChange={(e) => updateStage(i, { name: e.target.value })}
                  className="w-full min-h-[44px] rounded-lg border border-border bg-surface-2 px-2 text-sm"
                />
                <input
                  required
                  placeholder="Role (must match agent.role)"
                  value={s.role}
                  onChange={(e) => updateStage(i, { role: e.target.value })}
                  className="w-full min-h-[44px] rounded-lg border border-border bg-surface-2 px-2 text-sm"
                />
                <label className="flex items-center gap-2 text-xs min-h-[44px]">
                  <input
                    type="checkbox"
                    checked={!!s.requires_human_approval}
                    onChange={(e) => updateStage(i, { requires_human_approval: e.target.checked })}
                    className="h-4 w-4"
                  />
                  Requires human approval (HITL)
                </label>
              </div>
            ))}
          </div>

          <div className="flex gap-2 pt-2">
            <button type="button" onClick={() => setModalOpen(false)} className="min-h-[44px] flex-1 rounded-lg border border-border text-sm">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="min-h-[44px] flex-1 rounded-lg bg-accent text-sm font-medium text-white disabled:opacity-50">
              {saving ? 'Saving…' : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
