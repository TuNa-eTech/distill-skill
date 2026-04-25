import { useDashboardContext } from '../app/dashboardContext'
import { StatusBadge } from '../components/StatusBadge'
import { buildApiPath, useApiData } from '../features/dashboard/api'
import type { PipelineResponse } from '../features/dashboard/types'

export function PipelinePage() {
  const { role } = useDashboardContext()
  const pipelineState = useApiData<PipelineResponse>(
    buildApiPath('/api/pipeline', { role }),
  )

  if (pipelineState.loading) {
    return (
      <div className="empty-state">
        <div className="empty-state__card">
          <span className="page-eyebrow">Pipeline</span>
          <h2>Loading pipeline snapshot.</h2>
          <p>The stage rail is waiting for the current role-backed API response.</p>
        </div>
      </div>
    )
  }

  if (pipelineState.error || !pipelineState.data) {
    return (
      <div className="empty-state">
        <div className="empty-state__card">
          <span className="page-eyebrow">Pipeline</span>
          <h2>Unable to load the pipeline snapshot.</h2>
          <p>{pipelineState.error ?? 'The API did not return pipeline data.'}</p>
        </div>
      </div>
    )
  }

  const { badges, commands, filters, packSummary, stages, validation } =
    pipelineState.data

  return (
    <div className="page-grid">
      <section className="filter-bar">
        {filters.map((filter) => (
          <article key={filter.label} className="filter-tile">
            <span className="filter-tile__label">{filter.label}</span>
            <span className="filter-tile__value">{filter.value}</span>
          </article>
        ))}

        <div className="filter-bar__meta">
          {badges.map((badge) => (
            <StatusBadge key={badge.label} label={badge.label} tone={badge.tone} />
          ))}
        </div>
      </section>

      <div className="ops-layout">
        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">stage rail</span>
              <h2>Stage status</h2>
              <p>
                Each card is derived from the current DB snapshot, pack files, and
                live validation rules.
              </p>
            </div>
            <StatusBadge label={`${stages.length} stages`} tone="info" />
          </div>

          <div className="stage-rail">
            {stages.map((step, index) => (
              <article key={step.key} className="stage-card">
                <div className="stage-card__index">
                  {String(index + 1).padStart(2, '0')}
                </div>

                <div className="stage-card__body">
                  <div className="stage-card__header">
                    <div>
                      <span className="mono-kicker">stage</span>
                      <h3>{step.label}</h3>
                    </div>
                    <StatusBadge label={step.stateLabel} tone={step.tone} />
                  </div>

                  <p>{step.summary}</p>

                  <div className="stage-card__meta">
                    {step.facts.map((fact) => (
                      <span key={fact}>{fact}</span>
                    ))}
                  </div>

                  <div className="stage-card__detail">
                    <span className="chip">{step.description}</span>
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
                <span className="mono-kicker">pack output</span>
                <h2>Generated files</h2>
                <p>
                  This summary comes from the actual `pack.yaml`, `manifest.md`,
                  and skill module files.
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
                <span className="fact-tile__label">Generated at</span>
                <span className="fact-tile__value">
                  {packSummary.generatedAt || 'Unknown'}
                </span>
              </article>
              <article className="fact-tile">
                <span className="fact-tile__label">Filtered in</span>
                <span className="fact-tile__value">{String(packSummary.filteredIn)}</span>
              </article>
              <article className="fact-tile">
                <span className="fact-tile__label">Modules</span>
                <span className="fact-tile__value">{String(packSummary.moduleCount)}</span>
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
                <span className="mono-kicker">validation</span>
                <h2>Validator output</h2>
                <p>
                  The validation state is computed from
                  `distill_evolve.validate.validate_role_pack`.
                </p>
              </div>
              <StatusBadge
                label={validation.ok ? 'Validation pass' : 'Validation errors'}
                tone={validation.ok ? 'ok' : 'critical'}
              />
            </div>

            <div className="facts-grid">
              <article className="fact-tile">
                <span className="fact-tile__label">Modules checked</span>
                <span className="fact-tile__value">{String(validation.moduleCount)}</span>
              </article>
              <article className="fact-tile">
                <span className="fact-tile__label">Token estimate</span>
                <span className="fact-tile__value">{String(validation.totalTokens)}</span>
              </article>
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
                Validation passes on the current pack snapshot for this role.
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panel__header">
              <div>
                <span className="mono-kicker">command handoff</span>
                <h2>Local shortcuts</h2>
                <p>
                  The web shell stays read-only, but it shows the commands that
                  mutate the pipeline state.
                </p>
              </div>
              <StatusBadge label="Root Makefile" tone="ok" />
            </div>

            <div className="code-panel">
              <pre>{commands.join('\n')}</pre>
            </div>

            <div className="prototype-note">
              Trigger-run actions and writeback controls stay out of this UI until
              a real backend exists.
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
