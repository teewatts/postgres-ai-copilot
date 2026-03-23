"""
Parser for pasted PostgreSQL EXPLAIN / EXPLAIN ANALYZE text.

This module converts a narrow subset of text-based execution plans into
normalized internal plan objects. The first implementation is intentionally
limited to simple top-level plan shapes used by the MVP fixtures.
"""

from __future__ import annotations

import re

from app.schemas.plan import PlanNode, PlanSummary


# Match a simple top-level plan-node line such as:
# Seq Scan on users (cost=...) (actual time=...)
NODE_LINE_RE = re.compile(
    r"^(?P<node_type>.+?)\s+on\s+(?P<relation>\S+)\s+"
    r"\(cost=(?P<startup_cost>\d+(?:\.\d+)?)\.\.(?P<total_cost>\d+(?:\.\d+)?)\s+"
    r"rows=(?P<plan_rows>\d+(?:\.\d+)?)\s+width=(?P<width>\d+)\)"
    r"(?:\s+\(actual time=(?P<actual_start>\d+(?:\.\d+)?)\.\.(?P<actual_total>\d+(?:\.\d+)?)\s+"
    r"rows=(?P<actual_rows>\d+(?:\.\d+)?)\s+loops=(?P<loops>\d+)\))?"
)

# Capture optional detail lines that may appear under the main plan node.
FILTER_RE = re.compile(r"^\s*Filter:\s*(?P<filter>.+)$")
ROWS_REMOVED_RE = re.compile(r"^\s*Rows Removed by Filter:\s*(?P<rows>\d+(?:\.\d+)?)$")
PLANNING_TIME_RE = re.compile(r"^Planning Time:\s*(?P<ms>\d+(?:\.\d+)?)\s*ms$")
EXECUTION_TIME_RE = re.compile(r"^Execution Time:\s*(?P<ms>\d+(?:\.\d+)?)\s*ms$")


def parse_explain_text(plan_text: str) -> PlanSummary:
    """
    Parse a simplified text EXPLAIN plan into a normalized PlanSummary object.

    Args:
        plan_text: Raw pasted EXPLAIN or EXPLAIN ANALYZE text.

    Returns:
        A normalized plan summary containing the root node, timing metadata,
        and parser warnings when relevant information could not be extracted.
    """
    # Ignore blank lines so the parser only processes meaningful content.
    lines = [line.rstrip() for line in plan_text.splitlines() if line.strip()]
    warnings: list[str] = []

    root_node: PlanNode | None = None
    planning_time_ms: float | None = None
    execution_time_ms: float | None = None

    for line in lines:
        # Parse the first recognized plan-node line as the root node.
        # This matches the current MVP assumption of a simple plan shape.
        if root_node is None:
            node_match = NODE_LINE_RE.match(line.strip())
            if node_match:
                root_node = PlanNode(
                    node_type=node_match.group("node_type"),
                    relation_name=node_match.group("relation"),
                    startup_cost=float(node_match.group("startup_cost")),
                    total_cost=float(node_match.group("total_cost")),
                    plan_rows=float(node_match.group("plan_rows")),
                    actual_rows=float(node_match.group("actual_rows"))
                    if node_match.group("actual_rows")
                    else None,
                    actual_total_time=float(node_match.group("actual_total"))
                    if node_match.group("actual_total")
                    else None,
                )
                continue

        # Attach optional filter metadata to the root node when present.
        filter_match = FILTER_RE.match(line)
        if filter_match and root_node is not None:
            root_node.filter_condition = filter_match.group("filter")
            continue

        rows_removed_match = ROWS_REMOVED_RE.match(line)
        if rows_removed_match and root_node is not None:
            root_node.rows_removed_by_filter = float(rows_removed_match.group("rows"))
            continue

        # Capture plan-level timing lines that appear near the end of the output.
        planning_match = PLANNING_TIME_RE.match(line)
        if planning_match:
            planning_time_ms = float(planning_match.group("ms"))
            continue

        execution_match = EXECUTION_TIME_RE.match(line)
        if execution_match:
            execution_time_ms = float(execution_match.group("ms"))
            continue

    # Return a warning rather than failing hard when the plan shape is unsupported.
    if root_node is None:
        warnings.append("Could not parse a root plan node from the supplied EXPLAIN text.")

    return PlanSummary(
        format="text",
        raw_plan=plan_text,
        planning_time_ms=planning_time_ms,
        execution_time_ms=execution_time_ms,
        root_node=root_node,
        warnings=warnings,
    )