"""
Helpers for extracting predicate information from normalized execution plans.

This module contains lightweight utilities that infer likely filter columns
from parsed PostgreSQL plan conditions. The first implementation is narrow
and intentionally focused on simple equality predicates used in the MVP.
"""

from __future__ import annotations

import re


# Match simple predicate shapes such as:
#   (email = 'alice@example.com'::text)
#   ((email)::text = 'alice@example.com'::text)
#   (account_id = 123)
#
# The goal is not to fully parse SQL expressions. It is to identify the
# likely column on the left side of a simple equality predicate.
_SIMPLE_COLUMN_EQUALS_RE = re.compile(
    r"\(?\(?(?P<column>[a-zA-Z_][a-zA-Z0-9_]*)\)?(?:::[a-zA-Z0-9_ ]+)?\s*=\s*.+"
)


def extract_likely_filter_column(condition: str | None) -> str | None:
    """
    Extract the likely filtered column name from a simple plan condition.

    Args:
        condition: A filter or index condition string from a parsed plan node.

    Returns:
        The inferred column name if a simple predicate can be recognized,
        otherwise None.

    Notes:
        This implementation is intentionally conservative. It is meant to
        support common single-column equality predicates first.
    """
    if not condition:
        return None

    normalized = condition.strip()

    # Remove one layer of outer parentheses to simplify common plan output shapes.
    if normalized.startswith("(") and normalized.endswith(")"):
        normalized = normalized[1:-1].strip()

    match = _SIMPLE_COLUMN_EQUALS_RE.match(normalized)
    if not match:
        return None

    return match.group("column")