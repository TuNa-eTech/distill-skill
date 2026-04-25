import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router'
import type { DashboardContextValue } from './dashboardContext'
import { StatusBadge } from '../components/StatusBadge'
import { buildApiPath, useApiData } from '../features/dashboard/api'
import type { RolesResponse } from '../features/dashboard/types'

const navItems = [
  {
    to: '/',
    label: 'Overview',
    description: 'Current pack posture and source coverage.',
    index: '01',
  },
  {
    to: '/pipeline',
    label: 'Pipeline',
    description: 'Derived stage status from the live snapshot.',
    index: '02',
  },
  {
    to: '/review',
    label: 'Review',
    description: 'Persisted extraction inspection workbench.',
    index: '03',
  },
]

const pageCopy: Record<string, { eyebrow: string; heading: string; text: string }> = {
  '/': {
    eyebrow: 'Overview',
    heading: 'Control plane overview',
    text: 'Inspect current role-backed facts without drifting into a speculative control-plane shell.',
  },
  '/pipeline': {
    eyebrow: 'Pipeline',
    heading: 'Current stage posture',
    text: 'Each stage is derived from SQLite, generated pack files, and the live validation rules.',
  },
  '/review': {
    eyebrow: 'Review',
    heading: 'Extraction inspection',
    text: 'Focus on persisted extraction evidence instead of local-only moderation state.',
  },
}

function getPageKey(pathname: string) {
  if (pathname.startsWith('/pipeline')) {
    return '/pipeline'
  }

  if (pathname.startsWith('/review')) {
    return '/review'
  }

  return '/'
}

export function AppShell() {
  const location = useLocation()
  const navigate = useNavigate()
  const pageKey = getPageKey(location.pathname)
  const activePage = pageCopy[pageKey]
  const [navOpen, setNavOpen] = useState(false)
  const rolesState = useApiData<RolesResponse>(buildApiPath('/api/roles'))
  const roles = rolesState.data?.roles ?? []
  const requestedRole = new URLSearchParams(location.search).get('role')
  const fallbackRole = roles[0]?.role ?? 'mobile-dev'
  const activeRole = roles.some((item) => item.role === requestedRole)
    ? requestedRole || fallbackRole
    : requestedRole || fallbackRole
  const roleSummary = roles.find((item) => item.role === activeRole) ?? null

  useEffect(() => {
    setNavOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (rolesState.loading || roles.length === 0) {
      return
    }
    if (requestedRole === activeRole) {
      return
    }
    const nextSearch = new URLSearchParams(location.search)
    nextSearch.set('role', activeRole)
    navigate(
      {
        pathname: location.pathname,
        search: `?${nextSearch.toString()}`,
      },
      { replace: true },
    )
  }, [
    activeRole,
    location.pathname,
    location.search,
    navigate,
    requestedRole,
    roles.length,
    rolesState.loading,
  ])

  function buildRolePath(pathname: string) {
    const nextSearch = new URLSearchParams(location.search)
    nextSearch.set('role', activeRole)
    return `${pathname}?${nextSearch.toString()}`
  }

  function setRole(nextRole: string) {
    const nextSearch = new URLSearchParams(location.search)
    nextSearch.set('role', nextRole)
    navigate({
      pathname: location.pathname,
      search: `?${nextSearch.toString()}`,
    })
  }

  const outletContext: DashboardContextValue = {
    role: activeRole,
    roleLabel: roleSummary?.label ?? activeRole.replace('-', ' '),
    roles,
    roleSummary,
    rolesLoading: rolesState.loading,
    rolesError: rolesState.error,
  }

  return (
    <div className={`dashboard-shell${navOpen ? ' dashboard-shell--nav-open' : ''}`}>
      <aside className="dashboard-sidebar">
        <div className="dashboard-sidebar__brand">
          <NavLink to={buildRolePath('/')} className="brand-mark" end>
            <span className="brand-mark__glyph">D</span>
            <span className="brand-mark__text">Distill Dashboard</span>
          </NavLink>
        </div>

        <div className="sidebar-section">
          <span className="sidebar-section__label">Modules</span>
          <nav className="sidebar-nav" aria-label="Primary navigation">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={buildRolePath(item.to)}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `sidebar-nav__link${isActive ? ' sidebar-nav__link--active' : ''}`
                }
              >
                <span className="sidebar-nav__index">{item.index}</span>
                <span className="sidebar-nav__content">
                  <span className="sidebar-nav__label">{item.label}</span>
                  <span className="sidebar-nav__hint">{item.description}</span>
                </span>
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="sidebar-card">
          <span className="sidebar-section__label">Pilot scope</span>
          <div className="sidebar-card__title">Internal ops only</div>
          <p className="sidebar-card__text">
            The current surface reads directly from SQLite and generated pack files.
            Controls without a real backend path stay hidden.
          </p>
          <div className="cluster-summary">
            <span className="chip">{roleSummary?.role ?? activeRole}</span>
            <span className="chip">read-only</span>
            <span className="chip">sqlite + packs</span>
          </div>
        </div>
      </aside>

      {navOpen ? (
        <button
          className="sidebar-scrim"
          type="button"
          aria-label="Close navigation"
          onClick={() => setNavOpen(false)}
        />
      ) : null}

      <div className="dashboard-main">
        <header className="topbar">
          <div className="topbar__inner">
            <div className="topbar__primary">
              <button
                className="sidebar-toggle"
                type="button"
                aria-label="Toggle navigation"
                aria-expanded={navOpen}
                onClick={() => setNavOpen((current) => !current)}
              >
                Menu
              </button>

              <div className="topbar__copy">
                <span className="page-eyebrow">{activePage.eyebrow}</span>
                <h1 className="topbar__title">{activePage.heading}</h1>
                <p className="topbar__text">{activePage.text}</p>
              </div>
            </div>

            <div className="topbar__actions">
              <div className="topbar__status">
                <span className="inline-label inline-label--mono">
                  role {roleSummary?.role ?? activeRole}
                </span>
                {roleSummary ? (
                  <>
                    <span className="chip">scores {roleSummary.scoreCount}</span>
                    <span className="chip">
                      positive {roleSummary.positiveScoreCount}
                    </span>
                    <span className="chip">
                      extractions {roleSummary.extractionCount}
                    </span>
                    <StatusBadge
                      label={roleSummary.packAvailable ? 'Pack ready' : 'Pack missing'}
                      tone={roleSummary.packAvailable ? 'ok' : 'critical'}
                    />
                  </>
                ) : null}
                {!roleSummary && rolesState.loading ? (
                  <StatusBadge label="Loading roles" tone="muted" />
                ) : null}
                {!roleSummary && rolesState.error ? (
                  <StatusBadge label="Roles unavailable" tone="critical" />
                ) : null}
              </div>

              <label className="field-label field-label--inline topbar__role-picker">
                <span>Role</span>
                <select
                  value={activeRole}
                  onChange={(event) => setRole(event.currentTarget.value)}
                  disabled={roles.length === 0}
                >
                  {roles.length === 0 ? (
                    <option value={activeRole}>{activeRole}</option>
                  ) : (
                    roles.map((item) => (
                      <option key={item.role} value={item.role}>
                        {item.label}
                      </option>
                    ))
                  )}
                </select>
              </label>
            </div>
          </div>
        </header>

        <main className="dashboard-content">
          <Outlet context={outletContext} />
        </main>

        <footer className="dashboard-footer">
          <div className="dashboard-footer__inner">
            <span className="mono-kicker">control plane</span>
            <p>Built for pipeline visibility, extraction inspection, and pack trust.</p>
          </div>
        </footer>
      </div>
    </div>
  )
}
