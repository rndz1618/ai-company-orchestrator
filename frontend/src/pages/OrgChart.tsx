import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { Agent, Company } from '../types'
import { Network } from 'lucide-react'

type Node = Agent & { children: Node[] }

function buildTree(agents: Agent[]): Node[] {
  const map = new Map<number, Node>()
  for (const a of agents) {
    map.set(a.id, { ...a, children: [] })
  }
  const roots: Node[] = []
  for (const node of map.values()) {
    if (node.parent_id != null && map.has(node.parent_id)) {
      map.get(node.parent_id)!.children.push(node)
    } else {
      roots.push(node)
    }
  }
  const sortRec = (nodes: Node[]) => {
    nodes.sort((a, b) => a.name.localeCompare(b.name))
    nodes.forEach((n) => sortRec(n.children))
  }
  sortRec(roots)
  return roots
}

const statusDot: Record<string, string> = {
  active: 'bg-success',
  paused_budget: 'bg-danger',
  paused_manual: 'bg-warning',
  disabled: 'bg-muted',
}

function AgentNode({
  node,
  depth,
  agents,
  onSetParent,
  busyId,
}: {
  node: Node
  depth: number
  agents: Agent[]
  onSetParent: (agentId: number, parentId: number | null) => void
  busyId: number | null
}) {
  const candidates = agents.filter(
    (a) => a.id !== node.id && a.company_id === node.company_id && a.id !== node.parent_id
  )

  return (
    <li className="list-none">
      <div
        className="flex flex-col sm:flex-row sm:items-center gap-2 rounded-lg border border-border bg-surface-2 px-3 py-2.5"
        style={{ marginLeft: Math.min(depth, 4) * 12 }}
      >
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <span
            className={`h-2 w-2 rounded-full shrink-0 ${statusDot[node.status] || statusDot.disabled}`}
            title={node.status}
          />
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{node.name}</p>
            <p className="text-xs text-muted truncate">
              {node.role} · {node.provider}/{node.model}
            </p>
          </div>
        </div>
        <label className="flex items-center gap-2 text-xs text-muted shrink-0">
          <span className="hidden sm:inline">Reports to</span>
          <select
            disabled={busyId === node.id}
            value={node.parent_id ?? ''}
            onChange={(e) => {
              const v = e.target.value
              onSetParent(node.id, v === '' ? null : Number(v))
            }}
            className="min-h-[40px] rounded-lg border border-border bg-surface px-2 text-xs text-text max-w-[160px]"
          >
            <option value="">— Board / root —</option>
            {candidates.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} ({a.role})
              </option>
            ))}
          </select>
        </label>
      </div>
      {node.children.length > 0 && (
        <ul className="mt-2 space-y-2 border-l border-border/60 ml-3 sm:ml-4 pl-0">
          {node.children.map((c) => (
            <AgentNode
              key={c.id}
              node={c}
              depth={depth + 1}
              agents={agents}
              onSetParent={onSetParent}
              busyId={busyId}
            />
          ))}
        </ul>
      )}
    </li>
  )
}

export default function OrgChart() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [companies, setCompanies] = useState<Company[]>([])
  const [companyId, setCompanyId] = useState<number | 'all'>('all')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState<number | null>(null)

  const load = () => {
    setLoading(true)
    setError(null)
    Promise.all([api.agents.list(), api.companies.list()])
      .then(([a, c]) => {
        setAgents(a)
        setCompanies(c)
        if (companyId === 'all' && c.length === 1) setCompanyId(c[0].id)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const filtered = useMemo(
    () =>
      companyId === 'all'
        ? agents
        : agents.filter((a) => a.company_id === companyId),
    [agents, companyId]
  )

  const treesByCompany = useMemo(() => {
    const groups = new Map<number, Agent[]>()
    for (const a of filtered) {
      const list = groups.get(a.company_id) || []
      list.push(a)
      groups.set(a.company_id, list)
    }
    return [...groups.entries()].map(([cid, list]) => ({
      companyId: cid,
      name: companies.find((c) => c.id === cid)?.name || `Company #${cid}`,
      roots: buildTree(list),
    }))
  }, [filtered, companies])

  const setParent = async (agentId: number, parentId: number | null) => {
    setBusyId(agentId)
    setError(null)
    try {
      await api.agents.update(agentId, { parent_id: parentId })
      await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Network size={22} className="text-accent" />
            Org chart
          </h2>
          <p className="text-sm text-muted">
            Hierarchy via parent_id — Board sits above roots
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {companies.length > 0 && (
            <select
              value={companyId}
              onChange={(e) =>
                setCompanyId(e.target.value === 'all' ? 'all' : Number(e.target.value))
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
          <button
            type="button"
            onClick={load}
            className="min-h-[44px] rounded-lg border border-border px-3 text-sm text-muted hover:bg-surface-3"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
          {error}
        </div>
      )}
      {loading && <p className="text-sm text-muted">Loading…</p>}

      {!loading && treesByCompany.length === 0 && (
        <p className="text-sm text-muted">
          No agents yet. Hire agents first, then set reporting lines here.
        </p>
      )}

      {!loading &&
        treesByCompany.map((group) => (
          <section key={group.companyId} className="space-y-3">
            {treesByCompany.length > 1 && (
              <h3 className="text-sm font-medium text-muted">{group.name}</h3>
            )}
            <div className="rounded-xl border border-dashed border-border bg-surface/50 px-3 py-2 text-xs text-muted">
              Board (you)
            </div>
            <ul className="space-y-2">
              {group.roots.map((n) => (
                <AgentNode
                  key={n.id}
                  node={n}
                  depth={0}
                  agents={filtered.filter((a) => a.company_id === group.companyId)}
                  onSetParent={setParent}
                  busyId={busyId}
                />
              ))}
            </ul>
            {group.roots.length === 0 && (
              <p className="text-sm text-muted">No agents in this company.</p>
            )}
          </section>
        ))}
    </div>
  )
}
