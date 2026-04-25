export type DashboardTone = 'ok' | 'warn' | 'critical' | 'info' | 'muted'
export type PipelineState = 'ready' | 'partial' | 'empty' | 'missing'
export type SourceKind = 'gitlab_mr' | 'jira_issue' | 'confluence_page'

export type RoleOption = {
  role: string
  label: string
  primarySources: string[]
  primaryArtifactCount: number
  scoreCount: number
  positiveScoreCount: number
  extractionCount: number
  clusterCount: number
  packAvailable: boolean
  moduleCount: number
}

export type RolesResponse = {
  roles: RoleOption[]
}

export type FactItem = {
  label: string
  value: string
}

export type OverviewMetric = {
  label: string
  value: string
  meta: string
  accent: string
}

export type OverviewAlert = {
  title: string
  summary: string
  tone: DashboardTone
}

export type OverviewSourceHealth = {
  source: string
  items: string
  freshness: string
  note: string
  tone: DashboardTone
}

export type OverviewValidation = {
  ok: boolean
  errorCount: number
  errors: string[]
  moduleCount: number
  totalTokens: number
  tone: DashboardTone
  label: string
  facts: FactItem[]
}

export type PackSummary = {
  available: boolean
  role: string
  label: string
  version: string
  language: string | null
  generatedAt: string | null
  sourceWindow: string | null
  contributors: number
  sourceArtifacts: number
  filteredIn: number
  filteredOut: number
  modulesGenerated: number
  moduleCount: number
  moduleNames: string[]
  llmModel: string | null
}

export type OverviewResponse = {
  role: string
  roleLabel: string
  metrics: OverviewMetric[]
  alerts: OverviewAlert[]
  sourceHealth: OverviewSourceHealth[]
  snapshotFacts: FactItem[]
  validation: OverviewValidation
  packSummary: PackSummary
}

export type FilterTile = {
  label: string
  value: string
}

export type BadgeItem = {
  label: string
  tone: DashboardTone
}

export type PipelineStage = {
  key: string
  label: string
  description: string
  state: PipelineState
  stateLabel: string
  tone: DashboardTone
  summary: string
  facts: string[]
}

export type PipelineValidation = {
  ok: boolean
  errorCount: number
  errors: string[]
  moduleCount: number
  totalTokens: number
}

export type PipelineResponse = {
  role: string
  roleLabel: string
  filters: FilterTile[]
  badges: BadgeItem[]
  stages: PipelineStage[]
  packSummary: PackSummary
  validation: PipelineValidation
  commands: string[]
}

export type ReviewFilterOption = {
  value: string
  label: string
}

export type ReviewItem = {
  extractionId: number
  artifactId: number
  artifactExternalId: string
  title: string
  sourceKind: SourceKind
  sourceLabel: string
  score: number
  clusterName: string | null
  taskType: string
  domainTags: string[]
  patternCount: number
  topPatternSummary: string
  outcomeSignal: string
  extractedAt: string | null
  artifactUpdatedAt: string | null
}

export type ReviewListResponse = {
  role: string
  roleLabel: string
  filters: {
    sources: ReviewFilterOption[]
    clusters: ReviewFilterOption[]
  }
  summary: {
    visible: number
    total: number
    clustered: number
    unclustered: number
  }
  pagination: {
    limit: number
    offset: number
    total: number
  }
  items: ReviewItem[]
}

export type ReviewPattern = {
  kind: string
  summary: string
  evidenceExcerpt: string
  confidence: number
}

export type LinkedArtifact = {
  kind: SourceKind | string
  label: string
  externalId: string
  title: string
  linkType: string
  confidence: number
}

export type ReviewDetail = {
  extractionId: number
  artifactId: number
  artifactExternalId: string
  title: string
  sourceKind: SourceKind
  sourceLabel: string
  clusterName: string | null
  score: number
  scoreBreakdown: Record<string, number>
  taskType: string
  domainTags: string[]
  outcomeSignal: string
  patterns: ReviewPattern[]
  filesTouched: string[]
  linkedArtifacts: LinkedArtifact[]
  artifactMetadata: Record<string, unknown>
  artifactUpdatedAt: string | null
  extractedAt: string | null
  llmModel: string | null
  artifactWebUrl?: string
}
