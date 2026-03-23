from __future__ import annotations

from app.parsers.explain_text_parser import parse_explain_text
from app.schemas.input import ManualAnalysisInput
from app.schemas.output import (
    AnalysisOutput,
    BottleneckCategory,
    BottleneckSummary,
    ConfidenceLevel,
    EstimateMismatch,
    PriorityLevel,
    Recommendation,
    RecommendationType,
)


def analyze_manual_query(payload: ManualAnalysisInput) -> AnalysisOutput:
    plan_summary = parse_explain_text(payload.explain_plan or "")

    evidence: list[str] = []
    recommendations: list[Recommendation] = []
    estimate_mismatches: list[EstimateMismatch] = []
    category = BottleneckCategory.OTHER
    summary = "Analysis completed with limited heuristics."
    confidence = ConfidenceLevel.MEDIUM

    root = plan_summary.root_node

    if root is not None:
        if root.node_type.lower() == "seq scan":
            category = BottleneckCategory.SCAN
            evidence.append(f"Plan shows {root.node_type} on {root.relation_name}.")
            summary = "The query appears to rely on a sequential scan, which may be inefficient for selective filters."

        if root.rows_removed_by_filter and root.rows_removed_by_filter > 10000:
            evidence.append(
                f"Rows Removed by Filter is high at {int(root.rows_removed_by_filter)}."
            )

        if root.filter_condition:
            evidence.append(f"Filter condition detected: {root.filter_condition}")

        if (
            root.plan_rows is not None
            and root.actual_rows is not None
            and root.plan_rows > 0
            and root.actual_rows / root.plan_rows >= 10
        ):
            estimate_mismatches.append(
                EstimateMismatch(
                    node=root.node_type,
                    estimated_rows=root.plan_rows,
                    actual_rows=root.actual_rows,
                    severity=PriorityLevel.HIGH,
                    interpretation="Actual rows are much higher than estimated rows, which may indicate stale statistics or data skew.",
                )
            )

    sql_lower = payload.sql_query.lower()

    if "email" in sql_lower:
        recommendations.append(
            Recommendation(
                type=RecommendationType.INDEX,
                priority=PriorityLevel.HIGH,
                action="Consider adding an index on users(email).",
                rationale="The query filters on email and the plan indicates a sequential scan over a large number of rows.",
                risk="Additional storage and write overhead.",
                sql_candidate="CREATE INDEX CONCURRENTLY idx_users_email ON users (email);",
            )
        )
        confidence = ConfidenceLevel.HIGH

    if not evidence:
        evidence.append("No strong heuristic signal detected from the current input.")

    return AnalysisOutput(
        summary=summary,
        confidence=confidence,
        primary_bottleneck=BottleneckSummary(
            category=category,
            evidence=evidence,
        ),
        estimate_mismatches=estimate_mismatches,
        recommendations=recommendations,
        verification_steps=[
            "Review the proposed change in a non-production environment first.",
            "Re-run EXPLAIN ANALYZE after any index change.",
            "Check whether the new index benefits the broader workload, not just this one query."
        ],
        do_not_do=[
            "Do not apply index recommendations blindly without checking workload tradeoffs.",
            "Do not run CREATE INDEX directly on a production hot path without considering operational impact."
        ],
    )