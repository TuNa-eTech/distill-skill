import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router'
import { StatusBadge } from '../components/StatusBadge'

const navItems = [
  {
    to: '/',
    label: 'Overview',
    description: 'Health, source coverage, and pack posture.',
    index: '01',
  },
  {
    to: '/pipeline',
    label: 'Pipeline',
    description: 'Run state, step timing, and operator actions.',
    index: '02',
  },
  {
    to: '/review',
    label: 'Review',
    description: 'Queue triage, evidence, and correction loop.',
    index: '03',
  },
]

const pageCopy: Record<string, { eyebrow: string; heading: string; text: string }> = {
  '/': {
    eyebrow: 'Overview',
    heading: 'Control plane overview',
    text: 'Monitor ingestion health, review pressure, and pack readiness without drifting back into a landing-page layout.',
  },
  '/pipeline': {
    eyebrow: 'Pipeline',
    heading: 'Run state and operator handoff',
    text: 'Each stage should be legible enough to operate, debug, and rerun without leaving the dashboard shell.',
  },
  '/review': {
    eyebrow: 'Review',
    heading: 'Human correction loop',
    text: 'Keep the queue dense, calm, and hard to misuse while reviewers shape the final pack signal.',
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
  const pageKey = getPageKey(location.pathname)
  const activePage = pageCopy[pageKey]
  const [navOpen, setNavOpen] = useState(false)

  useEffect(() => {
    setNavOpen(false)
  }, [location.pathname])

  return (
    <div className={`dashboard-shell${navOpen ? ' dashboard-shell--nav-open' : ''}`}>
      <aside className="dashboard-sidebar">
        <div className="dashboard-sidebar__brand">
          <NavLink to="/" className="brand-mark" end>
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
                to={item.to}
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
            The current surface is optimized for one operator team managing
            role-scoped packs with human review still enforced.
          </p>
          <div className="cluster-summary">
            <span className="chip">mobile-dev</span>
            <span className="chip">human-reviewed</span>
            <span className="chip">sqlite source</span>
          </div>
        </div>

        <div className="sidebar-card sidebar-card--muted">
          <div className="sidebar-card__row">
            <span className="sidebar-section__label">Roadmap headroom</span>
            <StatusBadge label="Soon" tone="muted" />
          </div>
          <ul className="sidebar-card__list">
            <li>Packs preview surface</li>
            <li>Run history timeline</li>
            <li>Validation evidence browser</li>
          </ul>
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
                <span className="inline-label inline-label--mono">role mobile-dev</span>
                <span className="inline-label inline-label--mono">
                  window 2026-01-01 to today
                </span>
                <StatusBadge label="Last run 12m ago" tone="warn" />
              </div>

              <div className="topbar__buttons">
                <NavLink to="/review" className="button button--secondary">
                  Review queue
                </NavLink>
                <button className="button button--primary" type="button">
                  New run
                </button>
              </div>
            </div>
          </div>
        </header>

        <main className="dashboard-content">
          <Outlet />
        </main>

        <footer className="dashboard-footer">
          <div className="dashboard-footer__inner">
            <span className="mono-kicker">control plane</span>
            <p>Built for pipeline visibility, review discipline, and pack trust.</p>
          </div>
        </footer>
      </div>
    </div>
  )
}
