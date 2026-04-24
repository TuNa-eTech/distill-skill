from typing import Literal

from pydantic import BaseModel, Field

PatternKind = Literal["convention", "template", "anti-pattern", "decision"]


class Pattern(BaseModel):
    kind: PatternKind
    summary: str
    evidence_excerpt: str
    confidence: float = Field(ge=0.0, le=1.0)


class Extraction(BaseModel):
    artifact_id: int
    task_type: str
    domain_tags: list[str] = Field(default_factory=list)
    patterns: list[Pattern] = Field(default_factory=list)
    files_touched: list[str] = Field(default_factory=list)
    outcome_signal: str
