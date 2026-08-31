import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  Building2,
  Bot,
  ListTodo,
  Wallet,
  Menu,
  X,
} from 'lucide-react'
import { useState } from 'react'

const nav = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/companies', label: 'Companies', icon: Building2 },
  { to: '/agents', label: 'Agents', icon: Bot },
  { to: '/tasks', label: 'Tasks', icon: ListTodo },
  { to: '/budgets', label: 'Budgets', icon: Wallet },
]

export default function Layout() {
  const [open, setOpen] = useState(false)

  return (
    <div className="min-h-full flex flex-col md:flex-row bg-surface text-text">
      <aside className="hidden md:flex md:w-56 shrink-0 flex-col border-r border-border bg-surface-2">
        <div className="px-4 py-5 border-b border-border">
          <p className="text-xs uppercase tracking-wider text-muted">Board</p>
          <h1 className="text-lg font-semibold text-text">Orchestrator</h1>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm min-h-[44px] transition-colors ${
                  isActive
                    ? 'bg-accent/15 text-accent font-medium'
                    : 'text-muted hover:bg-surface-3 hover:text-text'
                }`
              }
            >
              <Icon size={18} strokeWidth={1.75} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <header className="md:hidden sticky top-0 z-20 flex items-center justify-between border-b border-border bg-surface-2 px-4 py-3">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-muted">Board</p>
          <h1 className="text-base font-semibold">Orchestrator</h1>
        </div>
        <button
          type="button"
          aria-label={open ? 'Close menu' : 'Open menu'}
          className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg hover:bg-surface-3"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </header>

      {open && (
        <div className="md:hidden border-b border-border bg-surface-2 px-3 py-2 space-y-1">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-3 text-sm min-h-[44px] ${
                  isActive ? 'bg-accent/15 text-accent font-medium' : 'text-muted'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </div>
      )}

      <main className="flex-1 overflow-auto pb-20 md:pb-6">
        <div className="mx-auto max-w-6xl p-4 md:p-6">
          <Outlet />
        </div>
      </main>

      <nav className="md:hidden fixed bottom-0 inset-x-0 z-20 border-t border-border bg-surface-2 pb-safe">
        <div className="flex justify-around">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 py-2 px-2 min-w-[56px] min-h-[52px] text-[10px] ${
                  isActive ? 'text-accent' : 'text-muted'
                }`
              }
            >
              <Icon size={20} strokeWidth={1.75} />
              <span>{label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
