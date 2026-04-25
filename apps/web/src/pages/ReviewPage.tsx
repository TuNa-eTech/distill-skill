import { useDeferredValue, useEffect, useState } from 'react'
import { useDashboardContext } from '../app/dashboardContext'
import { StatusBadge } from '../components/StatusBadge'
import { buildApiPath, useApiData } from '../features/dashboard/api'
import type { ReviewDetail, ReviewListResponse, SourceKind } from '../features/dashboard/types'

const EMPTY_REVIEW_ITEMS: ReviewListResponse['items'] = []

export function ReviewPage() {
  const { role } = useDashboardContext()
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sourceFilter, setSourceFilter] = useState<'all' | SourceKind>('all')
  const [clusterFilter, setClusterFilter] = useState('all')
  const deferredSearchQuery = useDeferredValue(searchQuery)
  const reviewListState = useApiData<ReviewListResponse>(
    buildApiPath('/api/review', {
      role,
      q: deferredSearchQuery,
      source: sourceFilter === 'all' ? undefined : sourceFilter,
      cluster: clusterFilter === 'all' ? undefined : clusterFilter,
      limit: 100,
    }),
  )
  const reviewItems = reviewListState.data?.items ?? EMPTY_REVIEW_ITEMS
  const reviewDetailState = useApiData<ReviewDetail>(
    selectedId === null ? null : buildApiPath(`/api/review/${selectedId}`, { role }),
  )

  useEffect(() => {
    if (reviewItems.some((item) => item.extractionId === selectedId)) {
      return
    }
    setSelectedId(reviewItems[0]?.extractionId ?? null)
  }, [reviewItems, selectedId])

  if (reviewListState.loading) {
    return (
      <div className="empty-state">
        <div className="empty-state__card">
          <span className="page-eyebrow">Review</span>
          <h2>Loading extraction workbench.</h2>
          <p>The page is fetching persisted extractions for the selected role.</p>
        </div>
      </div>
    )
  }

  if (reviewListState.error || !reviewListState.data) {
    return (
      <div className="empty-state">
        <div className="empty-state__card">
          <span className="page-eyebrow">Review</span>
          <h2>Unable to load the extraction workbench.</h2>
          <p>{reviewListState.error ?? 'The API did not return extraction data.'}</p>
        </div>
      </div>
    )
  }

  if (reviewItems.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state__card">
          <span className="page-eyebrow">Review</span>
          <h2>No extractions match the current filter set.</h2>
          <p>Clear the query or widen the source or cluster filter to inspect more data.</p>
        </div>
      </div>
    )
  }

  const selectedArtifact = reviewDetailState.data

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="panel__header">
          <div>
            <span className="mono-kicker">queue filters</span>
            <h2>Review workbench</h2>
            <p>
              Inspect persisted extractions, supporting evidence, and pack-relevant
              signals without pretending writeback exists.
            </p>
          </div>
          <StatusBadge label="Read-only" tone="info" />
        </div>

        <div className="review-toolbar">
          <label className="field-label field-label--inline review-toolbar__search">
            <span>Search</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search external ID, source kind, cluster, or payload"
            />
          </label>

          <label className="field-label field-label--inline">
            <span>Source</span>
            <select
              value={sourceFilter}
              onChange={(event) =>
                setSourceFilter(event.currentTarget.value as 'all' | SourceKind)
              }
            >
              {reviewListState.data.filters.sources.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field-label field-label--inline">
            <span>Cluster</span>
            <select
              value={clusterFilter}
              onChange={(event) => setClusterFilter(event.currentTarget.value)}
            >
              {reviewListState.data.filters.clusters.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <div className="review-toolbar__stats">
            <span className="chip">Visible {reviewListState.data.summary.visible}</span>
            <span className="chip">Total {reviewListState.data.summary.total}</span>
            <span className="chip">Clustered {reviewListState.data.summary.clustered}</span>
            <span className="chip">
              Unclustered {reviewListState.data.summary.unclustered}
            </span>
          </div>
        </div>
      </section>

      <div className="review-layout">
        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">queue</span>
              <h2>Extraction queue</h2>
              <p>Select an item to inspect task type, extracted patterns, and linked artifacts.</p>
            </div>
            <StatusBadge
              label={`${reviewListState.data.summary.visible} visible`}
              tone="muted"
            />
          </div>

          <div className="artifact-list">
            {reviewItems.map((artifact) => (
              <button
                key={artifact.extractionId}
                type="button"
                className={`artifact-row${
                  artifact.extractionId === selectedId ? ' artifact-row--active' : ''
                }`}
                onClick={() => setSelectedId(artifact.extractionId)}
              >
                <div className="artifact-row__top">
                  <h3>{artifact.title}</h3>
                  <StatusBadge label={artifact.outcomeSignal} tone="info" />
                </div>
                <div className="artifact-row__meta">
                  <span className="inline-label inline-label--mono">
                    extraction {artifact.extractionId}
                  </span>
                  <span className="inline-label inline-label--mono">
                    {artifact.artifactExternalId}
                  </span>
                  <span className="inline-label inline-label--mono">
                    score {artifact.score.toFixed(1)}
                  </span>
                  <span className="chip">
                    {artifact.clusterName ?? 'Unclustered'}
                  </span>
                </div>
                <p>{artifact.topPatternSummary}</p>
              </button>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">detail</span>
              <h2>Selected extraction</h2>
              <p>
                The detail panel stays factual: extracted patterns, linked
                artifacts, and score breakdown.
              </p>
            </div>
            {selectedArtifact ? (
              <StatusBadge label={selectedArtifact.sourceLabel} tone="info" />
            ) : (
              <StatusBadge label="Loading detail" tone="muted" />
            )}
          </div>

          {!selectedArtifact && reviewDetailState.loading ? (
            <div className="prototype-note">
              Loading extraction detail for the current selection.
            </div>
          ) : null}

          {!selectedArtifact && reviewDetailState.error ? (
            <div className="prototype-note">{reviewDetailState.error}</div>
          ) : null}

          {selectedArtifact ? (
            <div className="review-detail">
              <div className="review-detail__header">
                <div className="review-detail__meta">
                  <h3>{selectedArtifact.title}</h3>
                  <span className="inline-label inline-label--mono">
                    score {selectedArtifact.score.toFixed(1)}
                  </span>
                </div>
                <p className="review-detail__text">
                  {selectedArtifact.patterns[0]?.summary ||
                    'No extracted pattern summary is available for this item.'}
                </p>
                <div className="review-detail__stack">
                  <span className="inline-label inline-label--mono">
                    {selectedArtifact.artifactExternalId}
                  </span>
                  <span className="inline-label inline-label--mono">
                    extraction {selectedArtifact.extractionId}
                  </span>
                  <span className="inline-label">
                    {selectedArtifact.clusterName ?? 'Unclustered'}
                  </span>
                  <span className="inline-label">{selectedArtifact.taskType}</span>
                </div>
              </div>

              <div className="detail-grid">
                <article className="detail-card">
                  <div className="detail-card__label">Task and outcome</div>
                  <div className="facts-grid">
                    <article className="fact-tile">
                      <span className="fact-tile__label">Task type</span>
                      <span className="fact-tile__value">{selectedArtifact.taskType}</span>
                    </article>
                    <article className="fact-tile">
                      <span className="fact-tile__label">Outcome</span>
                      <span className="fact-tile__value">
                        {selectedArtifact.outcomeSignal}
                      </span>
                    </article>
                  </div>
                </article>

                <article className="detail-card">
                  <div className="detail-card__label">Domain tags</div>
                  {selectedArtifact.domainTags.length > 0 ? (
                    <div className="cluster-summary">
                      {selectedArtifact.domainTags.map((tag) => (
                        <span key={tag} className="chip">
                          {tag}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p>No domain tags were captured for this extraction.</p>
                  )}
                </article>
              </div>

              <div className="detail-grid">
                <article className="detail-card">
                  <div className="detail-card__label">Files touched</div>
                  {selectedArtifact.filesTouched.length > 0 ? (
                    <div className="cluster-summary">
                      {selectedArtifact.filesTouched.map((path) => (
                        <span key={path} className="chip">
                          {path}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p>No file paths were captured for this extraction.</p>
                  )}
                </article>

                <article className="detail-card">
                  <div className="detail-card__label">Score breakdown</div>
                  {Object.keys(selectedArtifact.scoreBreakdown).length > 0 ? (
                    <div className="facts-grid">
                      {Object.entries(selectedArtifact.scoreBreakdown).map(
                        ([label, value]) => (
                          <article key={label} className="fact-tile">
                            <span className="fact-tile__label">{label}</span>
                            <span className="fact-tile__value">
                              {value.toFixed(2)}
                            </span>
                          </article>
                        ),
                      )}
                    </div>
                  ) : (
                    <p>No score breakdown is available for this extraction.</p>
                  )}
                </article>
              </div>

              <article className="detail-card">
                <div className="detail-card__label">Linked artifacts</div>
                {selectedArtifact.linkedArtifacts.length > 0 ? (
                  <div className="attention-list">
                    {selectedArtifact.linkedArtifacts.map((item) => (
                      <article
                        key={`${item.kind}:${item.externalId}`}
                        className="attention-item"
                      >
                        <div className="attention-item__top">
                          <h3>{item.title}</h3>
                          <StatusBadge label={item.label} tone="info" />
                        </div>
                        <p>
                          {item.externalId} • {item.linkType} • confidence{' '}
                          {item.confidence.toFixed(2)}
                        </p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <p>No linked artifacts were found for this source item.</p>
                )}
              </article>

              <article className="detail-card">
                <div className="detail-card__label">Extracted patterns</div>
                {selectedArtifact.patterns.length > 0 ? (
                  <div className="attention-list">
                    {selectedArtifact.patterns.map((pattern, index) => (
                      <article
                        key={`${pattern.kind}-${pattern.summary}-${index}`}
                        className="attention-item"
                      >
                        <div className="attention-item__top">
                          <h3>{pattern.summary}</h3>
                          <StatusBadge
                            label={`${Math.round(pattern.confidence * 100)}%`}
                            tone="info"
                          />
                        </div>
                        <p>
                          {pattern.kind} •{' '}
                          {pattern.evidenceExcerpt || 'No evidence excerpt'}
                        </p>
                      </article>
                    ))}
                  </div>
                ) : (
                  <p>No extracted patterns were persisted for this item.</p>
                )}
              </article>

              <div className="control-row">
                {selectedArtifact.artifactWebUrl ? (
                  <a
                    className="button button--secondary"
                    href={selectedArtifact.artifactWebUrl}
                    rel="noreferrer"
                    target="_blank"
                  >
                    Open source artifact
                  </a>
                ) : null}
                <span className="chip">outcome {selectedArtifact.outcomeSignal}</span>
                <span className="chip">
                  extracted {selectedArtifact.extractedAt || 'Unknown'}
                </span>
              </div>
            </div>
          ) : null}
        </section>
      </div>
    </div>
  )
}
