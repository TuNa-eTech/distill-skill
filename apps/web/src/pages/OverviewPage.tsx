import { MetricCard } from '../components/MetricCard'
import { StatusBadge } from '../components/StatusBadge'
import {
  activityFeed,
  attentionItems,
  latestRun,
  overviewMetrics,
  packDefaults,
  sourceHealth,
} from '../features/dashboard/mockData'

const workflowSteps = [
  {
    label: 'Develop',
    accentClass: 'workflow-step--develop',
    description: 'Capture the real engineering traces that are worth learning from.',
  },
  {
    label: 'Preview',
    accentClass: 'workflow-step--preview',
    description: 'Review extracted patterns while ambiguity is still visible and reversible.',
  },
  {
    label: 'Ship',
    accentClass: 'workflow-step--ship',
    description: 'Only publish pack guidance once it survives operator scrutiny.',
  },
]

export function OverviewPage() {
  return (
    <div className="page-grid">
      <section className="stats-grid" aria-label="Overview metrics">
        {overviewMetrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </section>

      <div className="overview-grid">
        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">workflow rail</span>
              <h2>Develop to preview to ship</h2>
              <p>
                Accent colors stay reserved for workflow intent, while the rest of
                the dashboard remains monochrome and quiet.
              </p>
            </div>
            <StatusBadge label="Ops posture" tone="info" />
          </div>

          <div className="workflow-rail">
            {workflowSteps.map((step) => (
              <article
                key={step.label}
                className={`workflow-rail__step ${step.accentClass}`}
              >
                <span className="workflow-rail__label">{step.label}</span>
                <p>{step.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">latest run</span>
              <h2>Current production posture</h2>
              <p>The dashboard should foreground the current run before any deeper analysis.</p>
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
      </div>

      <div className="overview-grid">
        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">review pressure</span>
              <h2>Attention required</h2>
              <p>Operational gaps that matter before the next pack is trusted.</p>
            </div>
            <StatusBadge label="Needs review" tone="warn" />
          </div>

          <div className="attention-list">
            {attentionItems.map((item) => (
              <article key={item.title} className="attention-item">
                <div className="attention-item__top">
                  <h3>{item.title}</h3>
                  <StatusBadge label={item.tone} tone={item.tone} />
                </div>
                <p>{item.summary}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">source health</span>
              <h2>Ingest window health</h2>
              <p>How stable the current source window looks across each upstream system.</p>
            </div>
            <StatusBadge label="Updated today" tone="ok" />
          </div>

          <div className="source-health">
            {sourceHealth.map((item) => (
              <article key={item.source} className="source-health__item">
                <div className="source-health__row">
                  <div>
                    <h3>{item.source}</h3>
                    <p>{item.note}</p>
                  </div>
                  <StatusBadge label={item.freshness} tone={item.tone} />
                </div>
                <div className="source-health__value">{item.items}</div>
              </article>
            ))}
          </div>
        </section>
      </div>

      <div className="overview-grid overview-grid--support">
        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">pack stance</span>
              <h2>Current operating defaults</h2>
              <p>The shell should keep the accepted baseline visible while the pack system evolves.</p>
            </div>
            <StatusBadge label="Accepted baseline" tone="info" />
          </div>

          <div className="facts-grid">
            {packDefaults.map((item) => (
              <article key={item.label} className="fact-tile">
                <span className="fact-tile__label">{item.label}</span>
                <span className="fact-tile__value">{item.value}</span>
              </article>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">activity</span>
              <h2>Recent changes</h2>
              <p>Short operational deltas that deserve surface area in the control plane.</p>
            </div>
          </div>

          <div className="activity-list">
            {activityFeed.map((item) => (
              <article key={item} className="activity-item">
                {item}
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
