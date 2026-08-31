import { useEffect, useState } from 'react'
import { api, type CompanyCreate } from '../api/client'
import type { Company } from '../types'
import Modal from '../components/Modal'
import { Plus, Pencil, Trash2 } from 'lucide-react'

const emptyForm: CompanyCreate = { name: '', mission: '', monthly_budget: 500 }

export default function Companies() {
  const [items, setItems] = useState<Company[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Company | null>(null)
  const [form, setForm] = useState<CompanyCreate>(emptyForm)
  const [saving, setSaving] = useState(false)

  const load = () => {
    setLoading(true)
    setError(null)
    api.companies
      .list()
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setModalOpen(true)
  }

  const openEdit = (c: Company) => {
    setEditing(c)
    setForm({
      name: c.name,
      mission: c.mission || '',
      monthly_budget: c.monthly_budget,
    })
    setModalOpen(true)
  }

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) return
    setSaving(true)
    setError(null)
    try {
      if (editing) {
        await api.companies.update(editing.id, {
          name: form.name.trim(),
          mission: form.mission || null,
          monthly_budget: Number(form.monthly_budget) || 500,
        })
      } else {
        await api.companies.create({
          name: form.name.trim(),
          mission: form.mission || null,
          monthly_budget: Number(form.monthly_budget) || 500,
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

  const remove = async (c: Company) => {
    if (!confirm(`Soft-delete company "${c.name}"?`)) return
    setError(null)
    try {
      await api.companies.remove(c.id)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Companies</h2>
          <p className="text-sm text-muted">Virtual companies you direct as Board</p>
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
            className="min-h-[44px] inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 text-sm font-medium text-white hover:bg-accent-hover"
          >
            <Plus size={16} /> New
          </button>
        </div>
      </div>
      {error && <p className="text-sm text-danger">{error}</p>}
      {loading && <p className="text-sm text-muted">Loading…</p>}
      {!loading && (
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
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <h3 className="font-medium">{c.name}</h3>
                    {c.mission && (
                      <p className="text-xs text-muted mt-1 line-clamp-2">{c.mission}</p>
                    )}
                  </div>
                  <div className="flex shrink-0 gap-1">
                    <button
                      type="button"
                      aria-label="Edit company"
                      onClick={() => openEdit(c)}
                      className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg hover:bg-surface-3 text-muted"
                    >
                      <Pencil size={16} />
                    </button>
                    <button
                      type="button"
                      aria-label="Delete company"
                      onClick={() => remove(c)}
                      className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg hover:bg-danger/10 text-muted hover:text-danger"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
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
            <p className="text-sm text-muted col-span-full">
              No companies yet. Tap <strong>New</strong> to create one.
            </p>
          )}
        </div>
      )}

      <Modal
        title={editing ? 'Edit company' : 'New company'}
        open={modalOpen}
        onClose={() => setModalOpen(false)}
      >
        <form onSubmit={save} className="space-y-4">
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
            <span className="text-xs text-muted">Mission</span>
            <textarea
              value={form.mission || ''}
              onChange={(e) => setForm({ ...form, mission: e.target.value })}
              rows={3}
              className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-xs text-muted">Monthly budget (USD)</span>
            <input
              type="number"
              min={0}
              step={1}
              value={form.monthly_budget ?? 500}
              onChange={(e) =>
                setForm({ ...form, monthly_budget: Number(e.target.value) })
              }
              className="w-full min-h-[44px] rounded-lg border border-border bg-surface px-3 text-sm"
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
              {saving ? 'Saving…' : editing ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
