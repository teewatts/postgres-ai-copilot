"""
Helpers for inferring which database metadata should be fetched.

This module contains small inference utilities used by connected-mode
analysis to decide which tables are worth introspecting based on the
parsed execution plan.
"""

from __future__ import annotations

from app.schemas.plan import PlanSummary


def infer_primary_table(plan_summary: PlanSummary) -> tuple[str, str] | None:
    """
    Infer the primary table to inspect from the root plan node.

    Args:
        plan_summary: Parsed and normalized execution-plan data.

    Returns:
        A tuple of (schema_name, table_name) if a primary relation can be
        inferred, otherwise None.

    Notes:
        The initial implementation assumes the default 'public' schema when
        the plan does not provide schema-qualified relation information.
    """
    root = plan_summary.root_node
    if root is None or not root.relation_name:
        return None

    # The MVP assumes relation names are unqualified unless future parsing
    # enhancements detect schema-qualified names explicitly.
    return ("public", root.relation_name)