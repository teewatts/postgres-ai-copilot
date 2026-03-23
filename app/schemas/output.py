from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BottleneckCategory(str, Enum):
    SCAN = "scan"
    JOIN = "join"
    SORT = "sort"
    STATS = "stats"
    LOCKING = "locking"
    CONFIG = "config"
    OTHER = "other"


class RecommendationType(str, Enum):
    INDEX = "index"
    REWRITE = "rewrite"
    STATS = "stats"
    CONFIG = "config"
    INVESTIGATE = "investigate"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BottleneckSummary(BaseModel):
    category: BottleneckCategory
    evidence: list[str] = Field(default_factory=list)


class EstimateMismatch(BaseModel):
    node: str
    estimated_rows: float | None = None
    actual_rows: float | None = None
    severity: PriorityLevel
    interpretation: str


class Recommendation(BaseModel):
    type: RecommendationType
    priority: PriorityLevel
    action: str
    rationale: str
    risk: str | None = None
    sql_candidate: str | None = None


class AnalysisOutput(BaseModel):
    summary: str
    confidence: ConfidenceLevel
    primary_bottleneck: BottleneckSummary
    estimate_mismatches: list[EstimateMismatch] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    verification_steps: list[str] = Field(default_factory=list)
    do_not_do: list[str] = Field(default_factory=list)