export type Metric = {
  label: string
  value: string
  meta: string
  accent: string
}

export type AttentionItem = {
  title: string
  summary: string
  tone: 'ok' | 'warn' | 'critical' | 'info'
}

export type SourceHealth = {
  source: string
  items: string
  freshness: string
  note: string
  tone: 'ok' | 'warn' | 'critical' | 'info'
}

export type PipelineStep = {
  name: string
  description: string
  status: 'ok' | 'warn' | 'critical' | 'info'
  statusLabel: string
  duration: string
  output: string
  freshness: string
  nextAction: string
}

export type ReviewArtifact = {
  id: string
  title: string
  source: 'gitlab_mr' | 'jira_issue' | 'confluence_page'
  score: number
  cluster: string
  signal: string
  status: 'ready' | 'needs-review' | 'rejected'
  summary: string
  evidence: string[]
  note: string
}

export type RunFact = {
  label: string
  value: string
}

export const overviewMetrics: Metric[] = [
  {
    label: 'Artifacts ingested',
    value: '400',
    meta: '120 GitLab MRs, 200 Jira issues, 80 Confluence pages',
    accent: '#0f6d6d',
  },
  {
    label: 'Positive-score queue',
    value: '112',
    meta: 'Current role filter: mobile-dev',
    accent: '#b86835',
  },
  {
    label: 'Live extractions',
    value: '30',
    meta: '0 failures in the latest extraction batch',
    accent: '#284c7f',
  },
  {
    label: 'Pack modules',
    value: '4',
    meta: 'Validate pass on live pack baseline',
    accent: '#b8504f',
  },
]

export const attentionItems: AttentionItem[] = [
  {
    title: 'Link coverage is still sparse',
    summary: 'Only a small fraction of MR artifacts are enriched with Jira links.',
    tone: 'warn',
  },
  {
    title: 'Cluster review remains heuristic-assisted',
    summary: 'A deeper manual pass is still needed before relying on synthesis output.',
    tone: 'info',
  },
  {
    title: 'Validation evidence templates are empty',
    summary: 'The validator passes format checks, but human usefulness evidence is pending.',
    tone: 'critical',
  },
]

export const sourceHealth: SourceHealth[] = [
  {
    source: 'GitLab',
    items: '120 MRs',
    freshness: 'Updated today',
    note: 'Multi-repo ingest is usable but still discussion-heavy.',
    tone: 'ok',
  },
  {
    source: 'Jira',
    items: '200 issues',
    freshness: 'Updated today',
    note: 'Good enough for scoring, but BA quality still needs stronger live examples.',
    tone: 'ok',
  },
  {
    source: 'Confluence',
    items: '80 pages',
    freshness: 'Updated today',
    note: 'Useful for specs and narratives, but not yet wired into a dedicated UI flow.',
    tone: 'info',
  },
]

export const activityFeed = [
  'distill-validate now checks manifest hard rules with the same citation bar as skills.',
  'tester-manual pack regenerated after role-scoped extraction cleanup.',
  'React dashboard shell added under apps/web for the internal control plane.',
]

export const latestRun: {
  id: string
  headline: string
  note: string
  statusLabel: string
  tone: 'ok' | 'warn' | 'critical' | 'info'
  facts: RunFact[]
} = {
  id: 'RUN-2026-04-24-001',
  headline: 'Latest mobile-dev run is usable, but still needs manual cluster review.',
  note:
    'The automated path completed cleanly enough to inspect, but the control plane should still point operators toward link coverage and review depth before publish.',
  statusLabel: 'Manual follow-up',
  tone: 'warn',
  facts: [
    { label: 'Role', value: 'mobile-dev' },
    { label: 'Window', value: '2026-01-01 to today' },
    { label: 'Completed', value: '7 stages' },
    { label: 'Review queue', value: '3 artifacts' },
  ],
}

export const packDefaults = [
  { label: 'Pilot role', value: 'mobile-dev' },
  { label: 'Pack posture', value: 'Human reviewed' },
  { label: 'Module baseline', value: '4 curated modules' },
  { label: 'Source mix', value: 'GitLab, Jira, Confluence' },
]

export const pipelineFilters = [
  { label: 'Role', value: 'mobile-dev' },
  { label: 'Since', value: '2026-01-01' },
  { label: 'Until', value: 'today' },
  { label: 'Mode', value: 'internal pilot' },
]

export const pipelineSteps: PipelineStep[] = [
  {
    name: 'Ingest',
    description: 'Pull artifacts from GitLab, Jira, and Confluence into SQLite + blobs.',
    status: 'ok',
    statusLabel: 'Healthy',
    duration: '3m 12s',
    output: '400 source artifacts persisted.',
    freshness: 'Updated today',
    nextAction: 'Inspect source deltas',
  },
  {
    name: 'Link',
    description: 'Cross-reference artifacts by deterministic IDs and references.',
    status: 'warn',
    statusLabel: 'Sparse coverage',
    duration: '11s',
    output: '9 Jira-reference links found.',
    freshness: 'Needs operator check',
    nextAction: 'Review missing links',
  },
  {
    name: 'Score',
    description: 'Assign role-specific quality signals for candidate selection.',
    status: 'ok',
    statusLabel: 'Healthy',
    duration: '8s',
    output: '112 positive-score artifacts for mobile-dev.',
    freshness: 'Updated today',
    nextAction: 'Inspect top-ranked queue',
  },
  {
    name: 'Extract',
    description: 'Use the LLM layer to pull reusable patterns from top-ranked artifacts.',
    status: 'ok',
    statusLabel: 'Healthy',
    duration: '5m 06s',
    output: '30 extractions inserted, 0 failures.',
    freshness: 'Updated today',
    nextAction: 'Open review queue',
  },
  {
    name: 'Cluster',
    description: 'Group extractions into module-ready themes before synthesis.',
    status: 'warn',
    statusLabel: 'Manual assist',
    duration: 'Manual',
    output: '4 clusters, still heuristic-assisted.',
    freshness: 'Manual pass pending',
    nextAction: 'Confirm cluster assignments',
  },
  {
    name: 'Synthesize',
    description: 'Generate role-scoped pack modules and manifest from reviewed clusters.',
    status: 'ok',
    statusLabel: 'Healthy',
    duration: '41s',
    output: '4 live modules in packs/mobile-dev/v0.1.',
    freshness: 'Updated today',
    nextAction: 'Preview pack output',
  },
  {
    name: 'Validate',
    description: 'Check citation diversity and pack size budget before distribution.',
    status: 'ok',
    statusLabel: 'Pass',
    duration: '4s',
    output: 'Validation pass on the latest live pack.',
    freshness: 'Updated today',
    nextAction: 'Review evidence bar',
  },
]

export const reviewArtifacts: ReviewArtifact[] = [
  {
    id: 'MR-101',
    title: 'Payment flow state update',
    source: 'gitlab_mr',
    score: 4.5,
    cluster: 'state management',
    signal: 'Merged MR with clear async state transitions.',
    status: 'ready',
    summary:
      'Strong candidate for state-management guidance because it handles loading, error, and retry paths without duplicated widget state.',
    evidence: [
      'Cubit handles async UI states with explicit loading and error branches.',
      'Review comments reinforce a single source of truth pattern.',
    ],
    note: 'Keep this as a positive example for state transitions.',
  },
  {
    id: 'APP-123',
    title: 'Regression checklist for payment retries',
    source: 'jira_issue',
    score: 3.9,
    cluster: 'regression strategy',
    signal: 'High-signal defect thread with environment-specific reproduction.',
    status: 'needs-review',
    summary:
      'Good QA evidence, but still too domain-specific for a generic module without abstraction.',
    evidence: [
      'Environment and actual-vs-expected fields are complete.',
      'Discussion shows the missing retry path in the original test plan.',
    ],
    note: 'Needs one pass to de-app-specific language before pack inclusion.',
  },
  {
    id: 'PAGE-274698698',
    title: 'Payment reminders ADR',
    source: 'confluence_page',
    score: 3.5,
    cluster: 'navigation',
    signal: 'Clear rationale and edge-case framing, but source fit is mixed.',
    status: 'rejected',
    summary:
      'Useful narrative context, but it does not directly support a mobile navigation pattern yet.',
    evidence: [
      'The page references rollout and product concerns more than UI flow mechanics.',
      'No code-review style conventions can be extracted directly from this page.',
    ],
    note: 'Rejected in this prototype because the linkage is too loose.',
  },
]

export const clusterOptions = [
  'state management',
  'navigation',
  'platform integration',
  'code review conventions',
  'regression strategy',
]
