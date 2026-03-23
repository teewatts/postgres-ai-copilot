"""
PostgreSQL client helpers for connected-mode analysis.

This module provides focused helpers for connecting to PostgreSQL, retrieving
execution plans in JSON format, and fetching table metadata needed to improve
analysis quality. The first version remains read-only and intentionally limits
live analysis to plain EXPLAIN for safety.
"""

from __future__ import annotations

import json

import psycopg

from app.schemas.database_metadata import ColumnMetadata, IndexMetadata, TableMetadata


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


def get_table_columns(
    database_url: str,
    table_schema: str,
    table_name: str,
) -> list[ColumnMetadata]:
    """
    Fetch column metadata for a specific table from information_schema.

    Args:
        database_url: PostgreSQL connection string.
        table_schema: Schema name for the target table.
        table_name: Table name for the target table.

    Returns:
        A list of normalized column metadata objects.
    """
    query = """
        SELECT
            table_schema,
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
        ORDER BY ordinal_position
    """

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (table_schema, table_name))
            rows = cur.fetchall()

    return [
        ColumnMetadata(
            table_schema=row[0],
            table_name=row[1],
            column_name=row[2],
            data_type=row[3],
            is_nullable=(row[4] == "YES"),
        )
        for row in rows
    ]


def get_table_indexes(
    database_url: str,
    table_schema: str,
    table_name: str,
) -> list[IndexMetadata]:
    """
    Fetch index metadata for a specific table from pg_indexes.

    Args:
        database_url: PostgreSQL connection string.
        table_schema: Schema name for the target table.
        table_name: Table name for the target table.

    Returns:
        A list of normalized index metadata objects.
    """
    query = """
        SELECT
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = %s
          AND tablename = %s
        ORDER BY indexname
    """

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (table_schema, table_name))
            rows = cur.fetchall()

    return [
        IndexMetadata(
            schemaname=row[0],
            tablename=row[1],
            indexname=row[2],
            indexdef=row[3],
        )
        for row in rows
    ]


def get_table_metadata(
    database_url: str,
    table_schema: str,
    table_name: str,
) -> TableMetadata:
    """
    Fetch grouped table metadata for a specific table.

    Args:
        database_url: PostgreSQL connection string.
        table_schema: Schema name for the target table.
        table_name: Table name for the target table.

    Returns:
        A grouped table metadata object containing columns and indexes.
    """
    columns = get_table_columns(database_url, table_schema, table_name)
    indexes = get_table_indexes(database_url, table_schema, table_name)

    return TableMetadata(
        table_schema=table_schema,
        table_name=table_name,
        columns=columns,
        indexes=indexes,
    )