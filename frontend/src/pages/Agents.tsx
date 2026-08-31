import { useEffect, useState } from 'react'
import { api, type AgentCreate } from '../api/client'
import type { Agent, Company } from '../types'
import Modal from '../components/Modal'
import { Plus, Pencil, Trash2, Pause, Play } from 'lucide-react'

const statusStyle: Record<string, string> = {
  active: 'bg-success/15 text-success',
  paused_budget: 'bg-danger/15 text-danger',
  paused_manual: 'bg-warning/15 text-warning',
  disabled: 'bg-surface-3 text-muted',
}

const PROVIDERS = ['anthropic', 'openai', 'openclaw', 'local', 'custom']

const emptyForm = (companyId: number): AgentCreate => ({
  company_id: companyId,
  name: '',
  role: '',
  system_prompt: '',
  description: '',
  provider: 'anthropic',
  model: 'claude-3-5-sonnet-20241022',
  monthly_budget: 50,
})

export default function Agents() {
  const [items, setItems] = useState<Agent[]>([])
  const [companies, setCompanies] = useState<Company[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Agent | null>(null)
  const [form, setForm] = useState<AgentCreate>(emptyForm(0))
  const [saving, setSaving] = useState(false)

  const load = () => {
    setLoading(true)
    setError(null)
    Promise.all([api.agents.list(), api.companies.list()])
      .then(([a, c]) => {
        setItems(a)
        setCompanies(c)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const openCreate = () => {
    setEditing(null)
    const cid = companies[0]?.id ?? 0
    setForm(emptyForm(cid))
    setModalOpen(true)
  }

  const openEdit = (a: Agent) => {
    setEditing(a)
    setForm({
      company_id: a.company_id,
      name: a.name,
      role: a.role,
      system_prompt: a.system_prompt || '',
      description: a.description || '',
      provider: a.provider,
      model: a.model,
      monthly_budget: a.monthly_budget,
      parent_id: a.parent_id,
    })
    setModalOpen(true)
  }

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim() || !form.role.trim() || !form.company_id) return
    setSaving(true)
    setError(null)
    try {
      if (editing) {
        await api.agents.update(editing.id, {
          name: form.name.trim(),
          role: form.role.trim(),
          system_prompt: form.system_prompt || null,
          description: form.description || null,
          provider: form.provider,
          model: form.model,
          monthly_budget: Number(form.monthly_budget) || 50,
        })
      } else {
        await api.agents.create({
          company_id: form.company_id,
          name: form.name.trim(),
          role: form.role.trim(),
          system_prompt: form.system_prompt || null,
          description: form.description || null,
          provider: form.provider || 'anthropic',
          model: form.model || 'claude-3-5-sonnet-20241022',
          monthly_budget: Number(form.monthly_budget) || 50,
        })
      }
      setModalOpen(false)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  const remove = async (a: Agent) => {
    if (!confirm(`Soft-delete agent "${a.name}"?`)) return
    try {
      await api.agents.remove(a.id)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  const togglePause = async (a: Agent) => {
    try {
      if (a.status === 'active') {
        await api.agents.pause(a.id)
      } else {
        await api.agents.resume(a.id)
      }
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  const companyName = (id: number) => companies.find((c) => c.id === id)?.name || `#${id}`

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Agents</h2>
          <p className="text-sm text-muted">Roles, providers, and spend caps</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={load}
            className="min-h-[44px] rounded-lg border border-border px-3 text-sm text-muted hover:bg-surface-3"
          >
            Refresh
          </button>
          <button
            type="button"
            onClick={openCreate}
            disabled={companies.length === 0}
            className="min-h-[44px] inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50"
          >
            <Plus size={16} /> Hire
          </button>
        </div>
      </div>
      {companies.length === 0 && !loading && (
        <p className="text-sm text-warning">Create a company first before hiring agents.</p>
      )}
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
                  {a.role} · {a.provider}/{a.model} · {companyName(a.company_id)}
                </p>
                <p className="text-xs tabular-nums text-muted mt-0.5">
                  ${a.current_month_spend.toFixed(2)} / ${a.monthly_budget.toFixed(0)}
                </p>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <span
                  className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                    statusStyle[a.status] || statusStyle.disabled
                  }`}
                >
                  {a.status.replace(/_/g, ' ')}
                </span>
                <button
                  type="button"
                  aria-label={a.status === 'active' ? 'Pause agent' : 'Resume agent'}
                  onClick={() => togglePause(a)}
                  className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg hover:bg-surface-3 text-muted"
                >
                  {a.status === 'active' ? <Pause size={16} /> : <Play size={16} />}
                </button>
                <button
                  type="button"
                  aria-label="Edit agent"
                  onClick={() => openEdit(a)}
                  className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg hover:bg-surface-3 text-muted"
                >
                  <Pencil size={16} />
                </button>
                <button
                  type="button"
                  aria-label="Delete agent"
                  onClick={() => remove(a)}
                  className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg hover:bg-danger/10 text-muted hover:text-danger"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
          {items.length === 0 && !error && (
            <p className="px-4 py-6 text-sm text-muted text-center">
              No agents yet. Tap <strong>Hire</strong> to add one.
            </p>
          )}
        </div>
      )}

      <Modal
        title={editing ? 'Edit agent' : 'Hire agent'}
        open={modalOpen}
        onClose={() => setModalOpen(false)}
      >
        <form onSubmit={save} className="space-y-3">
          {!editing && (
            <label className="block space-y-1">
              <span className="text-xs text-muted">Company *</span>
              <select
                required
                value={form.company_id || ''}
                onChange={(e) =>
                  setForm({ ...form, company_id: Number(e.target.value) })
                }
                className="w-full min-h-[44px] rounded-lg border border-border bg-surface px-3 text-sm"
              >
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label className="block space-y-1">
            <span className="text-xs text-muted">Name *</span>
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full min-h-[44px] rounded-lg border border-border bg-surface px-3 text-sm"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-xs text-muted">Role * (must match workflow stage.role)</span>
            <input
              required
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
              placeholder="e.g. Researcher"
              className="w-full min-h-[44px] rounded-lg border border-border bg-surface px-3 text-sm"
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block space-y-1">
              <span className="text-xs text-muted">Provider</span>
              <select
                value={form.provider || 'anthropic'}
                onChange={(e) => setForm({ ...form, provider: e.target.value })}
                className="w-full min-h-[44px] rounded-lg border border-border bg-surface px-3 text-sm"
              >
                {PROVIDERS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </label>
            <label className="block space-y-1">
              <span className="text-xs text-muted">Monthly budget</span>
              <input
                type="number"
                min={0}
                step={1}
                value={form.monthly_budget ?? 50}
                onChange={(e) =>
                  setForm({ ...form, monthly_budget: Number(e.target.value) })
                }
                className="w-full min-h-[44px] rounded-lg border border-border bg-surface px-3 text-sm"
              />
            </label>
          </div>
          <label className="block space-y-1">
            <span className="text-xs text-muted">Model</span>
            <input
              value={form.model || ''}
              onChange={(e) => setForm({ ...form, model: e.target.value })}
              className="w-full min-h-[44px] rounded-lg border border-border bg-surface px-3 text-sm"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-xs text-muted">System prompt</span>
            <textarea
              value={form.system_prompt || ''}
              onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
              rows={4}
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm"
            />
          </label>
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="min-h-[44px] flex-1 rounded-lg border border-border text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="min-h-[44px] flex-1 rounded-lg bg-accent text-sm font-medium text-white disabled:opacity-50"
            >
              {saving ? 'Saving…' : editing ? 'Update' : 'Hire'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
