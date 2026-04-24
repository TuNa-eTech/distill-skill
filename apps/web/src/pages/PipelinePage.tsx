import { StatusBadge } from '../components/StatusBadge'
import {
  latestRun,
  pipelineFilters,
  pipelineSteps,
} from '../features/dashboard/mockData'

const operatorActions = [
  {
    title: 'Run full pipeline',
    note: 'Kick off the full ingest to validate chain for the current role window.',
    buttonLabel: 'Run all stages',
    buttonVariant: 'primary',
  },
  {
    title: 'Re-run validate',
    note: 'Repeat the final validation gate without touching the rest of the pipeline.',
    buttonLabel: 'Validate only',
    buttonVariant: 'secondary',
  },
  {
    title: 'Open review queue',
    note: 'Move straight into manual triage when extraction quality looks uncertain.',
    buttonLabel: 'Go to review',
    buttonVariant: 'secondary',
  },
] as const

export function PipelinePage() {
  return (
    <div className="page-grid">
      <section className="filter-bar">
        {pipelineFilters.map((filter) => (
          <article key={filter.label} className="filter-tile">
            <span className="filter-tile__label">{filter.label}</span>
            <span className="filter-tile__value">{filter.value}</span>
          </article>
        ))}

        <div className="filter-bar__meta">
          <StatusBadge label="Mock data" tone="muted" />
          <StatusBadge label="Human reviewed" tone="info" />
        </div>
      </section>

      <div className="ops-layout">
        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">stage rail</span>
              <h2>Stage status</h2>
              <p>Each card maps to one Distill CLI stage in the local pipeline chain.</p>
            </div>
            <StatusBadge label="7 stages" tone="info" />
          </div>

          <div className="stage-rail">
            {pipelineSteps.map((step, index) => (
              <article key={step.name} className="stage-card">
                <div className="stage-card__index">
                  {String(index + 1).padStart(2, '0')}
                </div>

                <div className="stage-card__body">
                  <div className="stage-card__header">
                    <div>
                      <span className="mono-kicker">stage</span>
                      <h3>{step.name}</h3>
                    </div>
                    <StatusBadge label={step.statusLabel} tone={step.status} />
                  </div>

                  <p>{step.description}</p>

                  <div className="stage-card__meta">
                    <span>Duration {step.duration}</span>
                    <span>{step.output}</span>
                    <span>{step.freshness}</span>
                  </div>

                  <div className="stage-card__detail">
                    <span className="chip">{step.nextAction}</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <div className="ops-sidebar">
          <section className="panel">
            <div className="panel__header">
              <div>
                <span className="mono-kicker">run summary</span>
                <h2>Latest run snapshot</h2>
                <p>The pipeline page should keep current run context pinned next to the stage rail.</p>
              </div>
              <StatusBadge label={latestRun.statusLabel} tone={latestRun.tone} />
            </div>

            <div className="run-highlight">
              <div className="run-highlight__heading">
                <div>
                  <span className="inline-label inline-label--mono">{latestRun.id}</span>
                  <h3>{latestRun.headline}</h3>
                </div>
              </div>
              <p>{latestRun.note}</p>
              <div className="facts-grid">
                {latestRun.facts.map((fact) => (
                  <article key={fact.label} className="fact-tile">
                    <span className="fact-tile__label">{fact.label}</span>
                    <span className="fact-tile__value">{fact.value}</span>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel__header">
              <div>
                <span className="mono-kicker">operator actions</span>
                <h2>Quick actions</h2>
                <p>Action hierarchy mirrors how an operator actually approaches the pipeline.</p>
              </div>
            </div>

            <div className="action-stack">
              {operatorActions.map((action) => (
                <article key={action.title} className="action-card">
                  <div>
                    <h3>{action.title}</h3>
                    <p>{action.note}</p>
                  </div>
                  <button
                    className={`button ${
                      action.buttonVariant === 'primary'
                        ? 'button--primary'
                        : 'button--secondary'
                    }`}
                    type="button"
                  >
                    {action.buttonLabel}
                  </button>
                </article>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel__header">
              <div>
                <span className="mono-kicker">command handoff</span>
                <h2>Local shortcuts</h2>
                <p>Repo-level commands already wired for the Python pipeline and the React shell.</p>
              </div>
              <StatusBadge label="Root Makefile" tone="ok" />
            </div>

            <div className="code-panel">
              <pre>{`make web-install
make web-dev

make ingest
make link
make score ROLE=mobile-dev
make extract ROLE=mobile-dev
make cluster ROLE=mobile-dev
make synthesize ROLE=mobile-dev
make validate ROLE=mobile-dev`}</pre>
            </div>

            <div className="prototype-note">
              The controls and summaries are still backed by mock data. The next
              backend pass should wire them to persisted runs, step logs, and
              real durations.
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
