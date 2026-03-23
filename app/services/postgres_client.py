"""
PostgreSQL client helpers for connected-mode analysis.

This module provides a small, focused interface for connecting to PostgreSQL
and retrieving execution plans in JSON format. The first version is read-only
and intentionally limited to plain EXPLAIN for safety.
"""

from __future__ import annotations

import json

import psycopg


def get_explain_json(database_url: str, sql_query: str, statement_timeout_ms: int = 5000) -> str:
    """
    Run EXPLAIN (FORMAT JSON) for a query and return the raw JSON text.

    Args:
        database_url: PostgreSQL connection string.
        sql_query: SQL statement to analyze.
        statement_timeout_ms: Timeout for the statement in milliseconds.

    Returns:
        A JSON string containing PostgreSQL EXPLAIN output.

    Raises:
        ValueError: If the query appears unsafe for the current connected-mode scope.
    """
    # Keep the first connected-mode implementation intentionally narrow.
    # We only allow SELECT statements here so the tool remains advisory.
    normalized_query = sql_query.lstrip().lower()
    if not normalized_query.startswith("select"):
        raise ValueError("Connected mode currently supports SELECT statements only.")

    explain_sql = f"EXPLAIN (FORMAT JSON) {sql_query}"

    # Use psycopg's standard connection and cursor pattern to run the query.
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            # Apply a local statement timeout so analysis queries do not hang indefinitely.
            cur.execute(f"SET statement_timeout = {statement_timeout_ms};")
            cur.execute(explain_sql)

            # PostgreSQL returns one row whose first column contains the JSON plan.
            result = cur.fetchone()

    if result is None:
        raise ValueError("No EXPLAIN result was returned by PostgreSQL.")

    plan_payload = result[0]

    # Depending on driver adaptation, psycopg may already return a Python object
    # for JSON data. Normalize it to a JSON string so the parser contract stays stable.
    if isinstance(plan_payload, str):
        return plan_payload

    return json.dumps(plan_payload)