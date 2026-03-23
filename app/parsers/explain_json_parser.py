"""
Parser for PostgreSQL EXPLAIN (FORMAT JSON) output.

This module converts PostgreSQL JSON execution-plan output into the normalized
internal plan models used by the analysis pipeline. JSON parsing is important
because it is the most natural format for the future connected-mode workflow.
"""

from __future__ import annotations

import json
from typing import Any

from app.schemas.plan import PlanNode, PlanSummary


def _parse_plan_node(node_payload: dict[str, Any]) -> PlanNode:
    """
    Convert a PostgreSQL JSON plan node into the internal PlanNode structure.

    Args:
        node_payload: A single plan-node object from PostgreSQL JSON EXPLAIN output.

    Returns:
        A normalized PlanNode with recursively parsed child nodes.
    """
    # PostgreSQL uses "Plans" to hold child plan nodes.
    child_nodes = [
        _parse_plan_node(child_payload)
        for child_payload in node_payload.get("Plans", [])
    ]

    return PlanNode(
        node_type=node_payload["Node Type"],
        relation_name=node_payload.get("Relation Name"),
        index_name=node_payload.get("Index Name"),
        startup_cost=node_payload.get("Startup Cost"),
        total_cost=node_payload.get("Total Cost"),
        plan_rows=node_payload.get("Plan Rows"),
        actual_rows=node_payload.get("Actual Rows"),
        actual_total_time=node_payload.get("Actual Total Time"),
        filter_condition=node_payload.get("Filter"),
        index_condition=node_payload.get("Index Cond"),
        join_filter=node_payload.get("Join Filter"),
        rows_removed_by_filter=node_payload.get("Rows Removed by Filter"),
        children=child_nodes,
    )


def parse_explain_json(plan_json: str) -> PlanSummary:
    """
    Parse PostgreSQL EXPLAIN (FORMAT JSON) output into a normalized PlanSummary.

    Args:
        plan_json: Raw JSON text returned by PostgreSQL EXPLAIN (FORMAT JSON).

    Returns:
        A normalized PlanSummary containing the root plan node, timing fields,
        and parser warnings if the JSON structure is missing expected fields.

    Raises:
        ValueError: If the input is not valid JSON or does not match the
            expected PostgreSQL EXPLAIN JSON structure.
    """
    try:
        parsed_payload = json.loads(plan_json)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON supplied for EXPLAIN plan.") from exc

    # PostgreSQL JSON EXPLAIN output is typically a one-element list.
    if not isinstance(parsed_payload, list) or not parsed_payload:
        raise ValueError("Expected EXPLAIN JSON payload to be a non-empty list.")

    top_level = parsed_payload[0]
    if not isinstance(top_level, dict) or "Plan" not in top_level:
        raise ValueError("Expected EXPLAIN JSON payload to contain a top-level 'Plan' object.")

    root_node = _parse_plan_node(top_level["Plan"])

    return PlanSummary(
        format="json",
        raw_plan=plan_json,
        planning_time_ms=top_level.get("Planning Time"),
        execution_time_ms=top_level.get("Execution Time"),
        root_node=root_node,
        warnings=[],
    )