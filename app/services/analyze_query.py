"""
Service-layer analysis logic for manual and connected query analysis.

This module contains the current analysis workflows. It parses supplied
execution plans or fetches them from PostgreSQL, applies a small set of
deterministic heuristics, and returns a normalized analysis result.
"""

from __future__ import annotations

from app.parsers.explain_json_parser import parse_explain_json
from app.parsers.explain_text_parser import parse_explain_text
from app.schemas.database_metadata import TableMetadata
from app.schemas.input import ConnectedAnalysisInput, ExplainFormat, ManualAnalysisInput
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
from app.services.metadata_inference import infer_primary_table
from app.services.postgres_client import get_explain_json, get_table_metadata
from app.services.predicate_extraction import extract_likely_filter_column


def _table_has_index_on_column(table_metadata: TableMetadata, column_name: str) -> bool:
    """
    Check whether any known index definition appears to cover the target column.

    Args:
        table_metadata: Metadata for the relevant table.
        column_name: Column name to look for inside index definitions.

    Returns:
        True if an existing index appears to include the target column,
        otherwise False.
    """
    target = f"({column_name}"
    fallback = f"{column_name})"

    for index in table_metadata.indexes:
        indexdef_lower = index.indexdef.lower()
        if target in indexdef_lower or fallback in indexdef_lower:
            return True

    return False


def _plan_uses_index_for_column(plan_summary, column_name: str) -> bool:
    """
    Check whether the parsed plan already appears to use an index on the target column.

    Args:
        plan_summary: Parsed and normalized execution-plan data.
        column_name: Column name to look for in the plan's index condition.

    Returns:
        True if the root node is an index-based scan and its index condition
        references the target column, otherwise False.
    """
    root = plan_summary.root_node
    if root is None:
        return False

    node_type_lower = root.node_type.lower()
    if "index scan" not in node_type_lower and "bitmap index scan" not in node_type_lower:
        return False

    if not root.index_condition:
        return False

    return column_name.lower() in root.index_condition.lower()


def _build_analysis_output(
    sql_query: str,
    plan_summary,
    table_metadata: TableMetadata | None = None,
) -> AnalysisOutput:
    """
    Build the current heuristic analysis result from a normalized plan summary.

    Args:
        sql_query: The SQL query being analyzed.
        plan_summary: Parsed and normalized plan data.
        table_metadata: Optional database metadata used to strengthen recommendations.

    Returns:
        A normalized analysis result containing heuristic findings,
        recommendations, and validation guidance.
    """
    evidence: list[str] = []
    recommendations: list[Recommendation] = []
    estimate_mismatches: list[EstimateMismatch] = []
    category = BottleneckCategory.OTHER
    summary = "Analysis completed with limited heuristics."
    confidence = ConfidenceLevel.MEDIUM

    root = plan_summary.root_node
    predicate_column: str | None = None

    if root is not None:
        root_node_type_lower = root.node_type.lower()

        if root_node_type_lower == "seq scan":
            category = BottleneckCategory.SEQ_SCAN
            evidence.append(f"Plan shows {root.node_type} on {root.relation_name}.")
            summary = (
                "The query appears to rely on a sequential scan, which may be "
                "inefficient for selective filters."
            )
        elif "index scan" in root_node_type_lower:
            category = BottleneckCategory.INDEX_SCAN
            evidence.append(f"Plan shows {root.node_type} on {root.relation_name}.")
            summary = (
                "The query is already using an index-based access path for the "
                "current predicate."
            )

        if root.rows_removed_by_filter and root.rows_removed_by_filter > 10000:
            evidence.append(
                f"Rows Removed by Filter is high at {int(root.rows_removed_by_filter)}."
            )

        if root.filter_condition:
            evidence.append(f"Filter condition detected: {root.filter_condition}")

        if root.index_condition:
            evidence.append(f"Index condition detected: {root.index_condition}")

        # Prefer index conditions first because they are often more specific in
        # indexed plans. Fall back to filter conditions for seq-scan cases.
        predicate_column = (
            extract_likely_filter_column(root.index_condition)
            or extract_likely_filter_column(root.filter_condition)
        )

        if predicate_column:
            evidence.append(f"Inferred predicate column: {predicate_column}")

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
                    interpretation=(
                        "Actual rows are much higher than estimated rows, which may "
                        "indicate stale statistics or data skew."
                    ),
                )
            )

    target_column = predicate_column
    target_table_name = root.relation_name if root is not None else "target_table"

    index_exists_for_target_column = False
    index_already_used_for_target_column = False

    if target_column:
        index_already_used_for_target_column = _plan_uses_index_for_column(
            plan_summary,
            target_column,
        )

    if table_metadata is not None:
        evidence.append(
            f"Fetched metadata for {table_metadata.table_schema}.{table_metadata.table_name}."
        )

        if target_column:
            index_exists_for_target_column = _table_has_index_on_column(
                table_metadata,
                target_column,
            )

            if index_exists_for_target_column:
                evidence.append(
                    f"An existing index appears to already include the {target_column} column."
                )

    if target_column and index_already_used_for_target_column:
        evidence.append(
            f"The current plan already uses an index condition on {target_column}."
        )
        recommendations.append(
            Recommendation(
                type=RecommendationType.INVESTIGATE,
                priority=PriorityLevel.LOW,
                action=f"No new {target_column} index recommendation is needed for this query.",
                rationale=(
                    f"The execution plan already uses an index condition on {target_column}, "
                    "so adding another index on the same column would likely be redundant."
                ),
                risk="Further tuning should focus on actual latency, row estimates, or broader workload behavior.",
            )
        )
        confidence = ConfidenceLevel.HIGH

    elif target_column and index_exists_for_target_column:
        recommendations.append(
            Recommendation(
                type=RecommendationType.INVESTIGATE,
                priority=PriorityLevel.MEDIUM,
                action=f"Investigate why the existing {target_column} index is not being used.",
                rationale=(
                    f"Metadata suggests an index already exists on {target_column}, but the "
                    "plan still shows a sequential scan."
                ),
                risk="The issue may be related to selectivity, statistics, or query shape.",
            )
        )

    elif target_column:
        recommendations.append(
            Recommendation(
                type=RecommendationType.INDEX,
                priority=PriorityLevel.HIGH,
                action=f"Consider adding an index on {target_table_name}({target_column}).",
                rationale=(
                    f"The query filters on {target_column} and the plan indicates a sequential "
                    "scan over a large number of rows."
                ),
                risk="Additional storage and write overhead.",
                sql_candidate=(
                    f"CREATE INDEX CONCURRENTLY idx_{target_table_name}_{target_column} "
                    f"ON {target_table_name} ({target_column});"
                ),
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
            "Check whether the new index benefits the broader workload, not just this one query.",
        ],
        do_not_do=[
            "Do not apply index recommendations blindly without checking workload tradeoffs.",
            "Do not run CREATE INDEX directly on a production hot path without considering operational impact.",
        ],
    )


def analyze_manual_query(payload: ManualAnalysisInput) -> AnalysisOutput:
    """
    Analyze a manually supplied SQL query and optional execution plan.

    Args:
        payload: Manual analysis input provided by the caller.

    Returns:
        A normalized analysis result derived from the supplied plan input.
    """
    if payload.explain_plan and payload.explain_format == ExplainFormat.JSON:
        plan_summary = parse_explain_json(payload.explain_plan)
    else:
        plan_summary = parse_explain_text(payload.explain_plan or "")

    return _build_analysis_output(payload.sql_query, plan_summary)


def analyze_connected_query(payload: ConnectedAnalysisInput) -> AnalysisOutput:
    """
    Analyze a query by retrieving its plan directly from PostgreSQL.

    Args:
        payload: Connected-mode analysis input with connection settings.

    Returns:
        A normalized analysis result derived from a live EXPLAIN (FORMAT JSON) call.
    """
    plan_json = get_explain_json(
        database_url=payload.connection.database_url,
        sql_query=payload.sql_query,
        statement_timeout_ms=payload.connection.statement_timeout_ms,
    )
    plan_summary = parse_explain_json(plan_json)

    table_metadata = None
    inferred_table = infer_primary_table(plan_summary)
    if inferred_table is not None:
        schema_name, table_name = inferred_table
        table_metadata = get_table_metadata(
            database_url=payload.connection.database_url,
            table_schema=schema_name,
            table_name=table_name,
        )

    return _build_analysis_output(payload.sql_query, plan_summary, table_metadata=table_metadata)