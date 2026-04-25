import { useDashboardContext } from '../app/dashboardContext'
import { MetricCard } from '../components/MetricCard'
import { StatusBadge } from '../components/StatusBadge'
import { buildApiPath, useApiData } from '../features/dashboard/api'
import type { OverviewResponse } from '../features/dashboard/types'

export function OverviewPage() {
  const { role } = useDashboardContext()
  const overviewState = useApiData<OverviewResponse>(
    buildApiPath('/api/overview', { role }),
  )

  if (overviewState.loading) {
    return (
      <div className="empty-state">
        <div className="empty-state__card">
          <span className="page-eyebrow">Overview</span>
          <h2>Loading dashboard snapshot.</h2>
          <p>The web shell is fetching the current SQLite and pack-backed summary.</p>
        </div>
      </div>
    )
  }

  if (overviewState.error || !overviewState.data) {
    return (
      <div className="empty-state">
        <div className="empty-state__card">
          <span className="page-eyebrow">Overview</span>
          <h2>Unable to load the current overview.</h2>
          <p>{overviewState.error ?? 'The API did not return overview data.'}</p>
        </div>
      </div>
    )
  }

  const { alerts, metrics, packSummary, snapshotFacts, sourceHealth, validation } =
    overviewState.data

  return (
    <div className="page-grid">
      <section className="stats-grid" aria-label="Overview metrics">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </section>

      <div className="overview-grid">
        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">current snapshot</span>
              <h2>Role-backed operating facts</h2>
              <p>
                These facts are derived directly from the current DB snapshot and
                generated pack metadata.
              </p>
            </div>
            <StatusBadge label={overviewState.data.roleLabel} tone="info" />
          </div>

          <div className="facts-grid">
            {snapshotFacts.map((fact) => (
              <article key={fact.label} className="fact-tile">
                <span className="fact-tile__label">{fact.label}</span>
                <span className="fact-tile__value">{fact.value}</span>
              </article>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">validation</span>
              <h2>Pack validity</h2>
              <p>
                The current token budget and citation validation result come from
                the real validator.
              </p>
            </div>
            <StatusBadge label={validation.label} tone={validation.tone} />
          </div>

          <div className="facts-grid">
            {validation.facts.map((fact) => (
              <article key={fact.label} className="fact-tile">
                <span className="fact-tile__label">{fact.label}</span>
                <span className="fact-tile__value">{fact.value}</span>
              </article>
            ))}
          </div>

          {validation.errors.length > 0 ? (
            <div className="attention-list">
              {validation.errors.map((error) => (
                <article key={error} className="attention-item">
                  <div className="attention-item__top">
                    <h3>Validation error</h3>
                    <StatusBadge label="critical" tone="critical" />
                  </div>
                  <p>{error}</p>
                </article>
              ))}
            </div>
          ) : (
            <div className="prototype-note">
              The current pack passes `distill-validate` and stays within the active token budget.
            </div>
          )}
        </section>
      </div>

      <div className="overview-grid">
        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">current signals</span>
              <h2>Observed gaps and cautions</h2>
              <p>
                These notices are derived from the actual snapshot, not from
                hand-written mock copy.
              </p>
            </div>
          </div>

          <div className="attention-list">
            {alerts.map((item) => (
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
              <h2>Current ingest coverage</h2>
              <p>
                Global source counts stay visible while the selected role focuses
                the rest of the shell.
              </p>
            </div>
          </div>

          <div className="source-health">
            {sourceHealth.map((item) => (
              <article key={item.source} className="source-health__item">
                <div className="source-health__row">
                  <div>
                    <h3>{item.source}</h3>
                    <p>{item.note}</p>
                  </div>
                  <StatusBadge label={item.tone} tone={item.tone} />
                </div>
                <div className="source-health__value">{item.items}</div>
                <p>{item.freshness}</p>
              </article>
            ))}
          </div>
        </section>
      </div>

      <div className="overview-grid overview-grid--support">
        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">pack output</span>
              <h2>Generated modules</h2>
              <p>
                This section only reflects files that actually exist under
                `packs/&lt;role&gt;/v0.1/`.
              </p>
            </div>
            <StatusBadge
              label={packSummary.available ? 'Pack found' : 'Pack missing'}
              tone={packSummary.available ? 'ok' : 'critical'}
            />
          </div>

          <div className="facts-grid">
            <article className="fact-tile">
              <span className="fact-tile__label">Version</span>
              <span className="fact-tile__value">{packSummary.version}</span>
            </article>
            <article className="fact-tile">
              <span className="fact-tile__label">Language</span>
              <span className="fact-tile__value">{packSummary.language || 'Unknown'}</span>
            </article>
            <article className="fact-tile">
              <span className="fact-tile__label">Modules generated</span>
              <span className="fact-tile__value">
                {String(packSummary.modulesGenerated)}
              </span>
            </article>
            <article className="fact-tile">
              <span className="fact-tile__label">Source window</span>
              <span className="fact-tile__value">
                {packSummary.sourceWindow || 'Unknown'}
              </span>
            </article>
          </div>

          <div className="cluster-summary">
            {packSummary.moduleNames.map((moduleName) => (
              <span key={moduleName} className="chip">
                {moduleName}
              </span>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">generation filter</span>
              <h2>Pack provenance signals</h2>
              <p>
                Contributor counts and filtered-in artifacts come from the
                generated `pack.yaml`.
              </p>
            </div>
          </div>

          <div className="facts-grid">
            <article className="fact-tile">
              <span className="fact-tile__label">Source artifacts</span>
              <span className="fact-tile__value">{String(packSummary.sourceArtifacts)}</span>
            </article>
            <article className="fact-tile">
              <span className="fact-tile__label">Filtered in</span>
              <span className="fact-tile__value">{String(packSummary.filteredIn)}</span>
            </article>
            <article className="fact-tile">
              <span className="fact-tile__label">Filtered out</span>
              <span className="fact-tile__value">{String(packSummary.filteredOut)}</span>
            </article>
            <article className="fact-tile">
              <span className="fact-tile__label">Contributors</span>
              <span className="fact-tile__value">{String(packSummary.contributors)}</span>
            </article>
            <article className="fact-tile">
              <span className="fact-tile__label">Generated at</span>
              <span className="fact-tile__value">
                {packSummary.generatedAt || 'Unknown'}
              </span>
            </article>
            <article className="fact-tile">
              <span className="fact-tile__label">LLM model</span>
              <span className="fact-tile__value">{packSummary.llmModel || 'Unknown'}</span>
            </article>
          </div>
        </section>
      </div>
    </div>
  )
}
