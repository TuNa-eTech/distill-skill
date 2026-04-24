import { useEffect, useState } from 'react'
import { StatusBadge } from '../components/StatusBadge'
import {
  clusterOptions,
  reviewArtifacts,
  type ReviewArtifact,
} from '../features/dashboard/mockData'

type ReviewStatus = 'ready' | 'needs-review' | 'rejected'
type ReviewSource = ReviewArtifact['source']

const statusTone: Record<ReviewStatus, 'ok' | 'warn' | 'critical'> = {
  ready: 'ok',
  'needs-review': 'warn',
  rejected: 'critical',
}

const sourceLabel: Record<ReviewSource, string> = {
  gitlab_mr: 'GitLab MR',
  jira_issue: 'Jira issue',
  confluence_page: 'Confluence page',
}

function matchesArtifact(
  artifact: ReviewArtifact,
  searchQuery: string,
  statusFilter: 'all' | ReviewStatus,
  sourceFilter: 'all' | ReviewSource,
) {
  const normalizedQuery = searchQuery.trim().toLowerCase()
  const matchesSearch =
    normalizedQuery.length === 0 ||
    artifact.title.toLowerCase().includes(normalizedQuery) ||
    artifact.signal.toLowerCase().includes(normalizedQuery) ||
    artifact.id.toLowerCase().includes(normalizedQuery)

  const matchesStatus =
    statusFilter === 'all' || artifact.status === statusFilter
  const matchesSource =
    sourceFilter === 'all' || artifact.source === sourceFilter

  return matchesSearch && matchesStatus && matchesSource
}

export function ReviewPage() {
  const [artifacts, setArtifacts] = useState(reviewArtifacts)
  const [selectedId, setSelectedId] = useState(reviewArtifacts[0]?.id ?? '')
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | ReviewStatus>('all')
  const [sourceFilter, setSourceFilter] = useState<'all' | ReviewSource>('all')

  useEffect(() => {
    const visibleSelection = artifacts
      .filter((artifact) =>
        matchesArtifact(artifact, searchQuery, statusFilter, sourceFilter),
      )
      .some((artifact) => artifact.id === selectedId)

    if (!visibleSelection) {
      setSelectedId(
        artifacts.find((artifact) =>
          matchesArtifact(artifact, searchQuery, statusFilter, sourceFilter),
        )?.id ?? '',
      )
    }
  }, [artifacts, searchQuery, selectedId, sourceFilter, statusFilter])

  const visibleArtifacts = artifacts.filter((artifact) =>
    matchesArtifact(artifact, searchQuery, statusFilter, sourceFilter),
  )

  const selectedArtifact =
    visibleArtifacts.find((artifact) => artifact.id === selectedId) ??
    visibleArtifacts[0]

  function updateSelectedArtifact(update: Partial<ReviewArtifact>) {
    setArtifacts((current) =>
      current.map((artifact) =>
        artifact.id === selectedId ? { ...artifact, ...update } : artifact,
      ),
    )
  }

  if (!selectedArtifact) {
    return (
      <div className="empty-state">
        <div className="empty-state__card">
          <span className="page-eyebrow">Review</span>
          <h2>No artifacts match the current filter set.</h2>
          <p>Clear the query or widen the status filter to resume triage.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page-grid">
      <section className="panel">
        <div className="panel__header">
          <div>
            <span className="mono-kicker">queue filters</span>
            <h2>Review workbench</h2>
            <p>Compact filters on top, queue on the left, evidence and actions on the right.</p>
          </div>
          <StatusBadge label="Prototype" tone="info" />
        </div>

        <div className="review-toolbar">
          <label className="field-label field-label--inline review-toolbar__search">
            <span>Search</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search title, signal, or ID"
            />
          </label>

          <label className="field-label field-label--inline">
            <span>Status</span>
            <select
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(event.target.value as 'all' | ReviewStatus)
              }
            >
              <option value="all">All statuses</option>
              <option value="ready">Ready</option>
              <option value="needs-review">Needs review</option>
              <option value="rejected">Rejected</option>
            </select>
          </label>

          <label className="field-label field-label--inline">
            <span>Source</span>
            <select
              value={sourceFilter}
              onChange={(event) =>
                setSourceFilter(event.target.value as 'all' | ReviewSource)
              }
            >
              <option value="all">All sources</option>
              <option value="gitlab_mr">GitLab MR</option>
              <option value="jira_issue">Jira issue</option>
              <option value="confluence_page">Confluence page</option>
            </select>
          </label>

          <div className="review-toolbar__stats">
            <span className="chip">Visible {visibleArtifacts.length}</span>
            <span className="chip">
              Needs review{' '}
              {
                artifacts.filter((artifact) => artifact.status === 'needs-review')
                  .length
              }
            </span>
            <span className="chip">
              Rejected{' '}
              {artifacts.filter((artifact) => artifact.status === 'rejected').length}
            </span>
          </div>
        </div>
      </section>

      <div className="review-layout">
        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">queue</span>
              <h2>Artifact queue</h2>
              <p>Select an item to inspect signal, evidence, and working note.</p>
            </div>
            <StatusBadge label={`${visibleArtifacts.length} visible`} tone="muted" />
          </div>

          <div className="artifact-list">
            {visibleArtifacts.map((artifact) => (
              <button
                key={artifact.id}
                type="button"
                className={`artifact-row${
                  artifact.id === selectedId ? ' artifact-row--active' : ''
                }`}
                onClick={() => setSelectedId(artifact.id)}
              >
                <div className="artifact-row__top">
                  <h3>{artifact.title}</h3>
                  <StatusBadge
                    label={artifact.status}
                    tone={statusTone[artifact.status]}
                  />
                </div>
                <div className="artifact-row__meta">
                  <span className="inline-label inline-label--mono">{artifact.id}</span>
                  <span className="inline-label inline-label--mono">
                    {sourceLabel[artifact.source]}
                  </span>
                  <span className="inline-label inline-label--mono">
                    score {artifact.score.toFixed(1)}
                  </span>
                  <span className="chip">{artifact.cluster}</span>
                </div>
                <p>{artifact.signal}</p>
              </button>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel__header">
            <div>
              <span className="mono-kicker">detail</span>
              <h2>Selected artifact</h2>
              <p>This panel models the lightweight edit loop for operators.</p>
            </div>
            <StatusBadge
              label={selectedArtifact.status}
              tone={statusTone[selectedArtifact.status]}
            />
          </div>

          <div className="review-detail">
            <div className="review-detail__header">
              <div className="review-detail__meta">
                <h3>{selectedArtifact.title}</h3>
                <span className="inline-label inline-label--mono">
                  score {selectedArtifact.score.toFixed(1)}
                </span>
              </div>
              <p className="review-detail__text">{selectedArtifact.summary}</p>
              <div className="review-detail__stack">
                <span className="inline-label inline-label--mono">{selectedArtifact.id}</span>
                <span className="inline-label inline-label--mono">
                  {sourceLabel[selectedArtifact.source]}
                </span>
                <span className="inline-label">{selectedArtifact.cluster}</span>
              </div>
            </div>

            <div className="detail-grid">
              <article className="detail-card">
                <div className="detail-card__label">Signal</div>
                <div>{selectedArtifact.signal}</div>
              </article>

              <article className="detail-card">
                <div className="detail-card__label">Evidence</div>
                <div className="attention-list">
                  {selectedArtifact.evidence.map((item) => (
                    <div key={item} className="attention-item">
                      {item}
                    </div>
                  ))}
                </div>
              </article>
            </div>

            <div className="review-actions">
              <label className="field-label">
                <span>Cluster assignment</span>
                <select
                  value={selectedArtifact.cluster}
                  onChange={(event) =>
                    updateSelectedArtifact({ cluster: event.target.value })
                  }
                >
                  {clusterOptions.map((cluster) => (
                    <option key={cluster} value={cluster}>
                      {cluster}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field-label">
                <span>Reviewer note</span>
                <textarea
                  value={selectedArtifact.note}
                  onChange={(event) =>
                    updateSelectedArtifact({ note: event.target.value })
                  }
                />
              </label>

              <div className="control-row">
                <button
                  className="button button--primary"
                  type="button"
                  onClick={() => updateSelectedArtifact({ status: 'ready' })}
                >
                  Mark ready
                </button>
                <button
                  className="button button--secondary"
                  type="button"
                  onClick={() => updateSelectedArtifact({ status: 'needs-review' })}
                >
                  Needs review
                </button>
                <button
                  className="button button--secondary button--critical"
                  type="button"
                  onClick={() => updateSelectedArtifact({ status: 'rejected' })}
                >
                  Reject
                </button>
              </div>

              <div className="prototype-note">
                These edits are local UI state for now. The next backend step is
                an `extraction_reviews` model plus endpoints for assign, reject,
                and note actions.
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
