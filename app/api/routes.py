from fastapi import APIRouter

from app.schemas.input import ManualAnalysisInput
from app.schemas.output import (
    AnalysisOutput,
    BottleneckCategory,
    BottleneckSummary,
    ConfidenceLevel,
    PriorityLevel,
    Recommendation,
    RecommendationType,
)

router = APIRouter()


@router.post("/analyze", response_model=AnalysisOutput)
def analyze_query(payload: ManualAnalysisInput) -> AnalysisOutput:
    sql_lower = payload.sql_query.lower()
    plan_text = (payload.explain_plan or "").lower()

    evidence: list[str] = []
    recommendations: list[Recommendation] = []
    summary = "Analysis completed with limited heuristics."
    category = BottleneckCategory.OTHER

    if "seq scan" in plan_text:
        category = BottleneckCategory.SCAN
        evidence.append("Execution plan includes a sequential scan.")
        summary = "The query appears to rely on a sequential scan, which may be inefficient for selective filters."

    if "where email" in sql_lower or "email =" in sql_lower:
        evidence.append("The query filters on email.")
        recommendations.append(
            Recommendation(
                type=RecommendationType.INDEX,
                priority=PriorityLevel.HIGH,
                action="Consider adding an index on users(email).",
                rationale="A selective email predicate often benefits from an index when the table is large.",
                risk="Additional storage and write overhead.",
                sql_candidate="CREATE INDEX CONCURRENTLY idx_users_email ON users (email);",
            )
        )

    if not evidence:
        evidence.append("No strong heuristic signal detected from the current input.")

    return AnalysisOutput(
        summary=summary,
        confidence=ConfidenceLevel.MEDIUM,
        primary_bottleneck=BottleneckSummary(
            category=category,
            evidence=evidence,
        ),
        recommendations=recommendations,
        verification_steps=[
            "Review the proposed change in a non-production environment first.",
            "Re-run EXPLAIN ANALYZE after any index change."
        ],
        do_not_do=[
            "Do not apply index recommendations blindly without checking workload tradeoffs."
        ],
    )