"""
Streamlit UI for Postgres AI Copilot.

This module provides a lightweight interactive interface for the current
analysis workflows. It is intended for local demos and development, and
it reuses the existing service-layer functions directly.
"""

from __future__ import annotations

import json

import streamlit as st
from pydantic import ValidationError

from app.schemas.input import (
    ConnectedAnalysisInput,
    ConnectionSettings,
    ExplainFormat,
    ManualAnalysisInput,
)
from app.services.analyze_query import analyze_connected_query, analyze_manual_query


def _render_analysis_result(result) -> None:
    """
    Render a normalized analysis result in the Streamlit UI.

    Args:
        result: The AnalysisOutput object returned by the service layer.
    """
    st.subheader("Analysis Summary")
    st.write(result.summary)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Confidence", result.confidence.value)
    with col2:
        st.metric("Category", result.primary_bottleneck.category.value)

    st.subheader("Evidence")
    for item in result.primary_bottleneck.evidence:
        st.write(f"- {item}")

    if result.estimate_mismatches:
        st.subheader("Estimate Mismatches")
        for mismatch in result.estimate_mismatches:
            st.write(f"- Node: {mismatch.node}")
            st.write(f"  - Estimated rows: {mismatch.estimated_rows}")
            st.write(f"  - Actual rows: {mismatch.actual_rows}")
            st.write(f"  - Severity: {mismatch.severity.value}")
            st.write(f"  - Interpretation: {mismatch.interpretation}")

    st.subheader("Recommendations")
    if result.recommendations:
        for rec in result.recommendations:
            with st.expander(f"{rec.type.value.upper()} | {rec.priority.value.upper()} | {rec.action}"):
                st.write(f"**Rationale:** {rec.rationale}")
                if rec.risk:
                    st.write(f"**Risk:** {rec.risk}")
                if rec.sql_candidate:
                    st.code(rec.sql_candidate, language="sql")
    else:
        st.write("No recommendations generated.")

    st.subheader("Verification Steps")
    for step in result.verification_steps:
        st.write(f"- {step}")

    st.subheader("Do Not Do")
    for item in result.do_not_do:
        st.write(f"- {item}")


def _manual_mode() -> None:
    """
    Render the manual analysis workflow.

    This mode accepts pasted SQL and optional EXPLAIN plan content.
    """
    st.header("Manual Analysis")

    sql_query = st.text_area(
        "SQL Query",
        height=140,
        placeholder="SELECT id, email, created_at FROM users WHERE email = 'alice@example.com';",
    )

    explain_format_label = st.selectbox(
        "EXPLAIN Format",
        options=["text", "json"],
        index=0,
    )

    explain_plan = st.text_area(
        "EXPLAIN Plan",
        height=240,
        placeholder="Paste EXPLAIN or EXPLAIN (FORMAT JSON) output here",
    )

    schema_ddl = st.text_area(
        "Schema DDL (optional)",
        height=140,
        placeholder="CREATE TABLE users (...);",
    )

    index_definitions = st.text_area(
        "Index Definitions (optional)",
        height=120,
        placeholder="CREATE INDEX ...;",
    )

    notes = st.text_area(
        "Notes (optional)",
        height=100,
        placeholder="Any additional context for the analysis",
    )

    if st.button("Run Manual Analysis", type="primary"):
        try:
            payload = ManualAnalysisInput(
                mode="manual",
                sql_query=sql_query,
                explain_plan=explain_plan or None,
                explain_format=(
                    ExplainFormat.JSON
                    if explain_format_label == "json"
                    else ExplainFormat.TEXT
                ),
                schema_ddl=schema_ddl or None,
                index_definitions=index_definitions or None,
                notes=notes or None,
            )
            result = analyze_manual_query(payload)
            _render_analysis_result(result)
        except ValidationError as exc:
            st.error("Input validation failed.")
            st.code(str(exc))
        except Exception as exc:
            st.error("Analysis failed.")
            st.code(str(exc))


def _connected_mode() -> None:
    """
    Render the connected analysis workflow.

    This mode connects to PostgreSQL, fetches a live JSON plan, and analyzes it.
    """
    st.header("Connected Analysis")

    database_url = st.text_input(
        "Database URL",
        type="password",
        placeholder="postgresql://postgres:password@localhost:5433/postgres_ai_copilot_demo",
    )

    sql_query = st.text_area(
        "SQL Query",
        height=140,
        placeholder="SELECT id, email, created_at FROM users WHERE email = 'alice@example.com';",
    )

    statement_timeout_ms = st.number_input(
        "Statement Timeout (ms)",
        min_value=100,
        max_value=60000,
        value=5000,
        step=100,
    )

    if st.button("Run Connected Analysis", type="primary"):
        try:
            payload = ConnectedAnalysisInput(
                mode="connected",
                sql_query=sql_query,
                connection=ConnectionSettings(
                    database_url=database_url,
                    statement_timeout_ms=int(statement_timeout_ms),
                    allow_explain_analyze=False,
                    allow_non_select=False,
                ),
            )
            result = analyze_connected_query(payload)
            _render_analysis_result(result)
        except ValidationError as exc:
            st.error("Input validation failed.")
            st.code(str(exc))
        except Exception as exc:
            st.error("Connected analysis failed.")
            st.code(str(exc))


def main() -> None:
    """
    Run the Streamlit application.
    """
    st.set_page_config(page_title="Postgres AI Copilot", layout="wide")
    st.title("Postgres AI Copilot")
    st.caption("AI-assisted PostgreSQL query plan analysis and tuning recommendations")

    st.write(
        "Use manual mode to paste a query plan, or connected mode to fetch a live "
        "plan from PostgreSQL with EXPLAIN (FORMAT JSON)."
    )

    mode = st.radio(
        "Choose analysis mode",
        options=["Manual", "Connected"],
        horizontal=True,
    )

    if mode == "Manual":
        _manual_mode()
    else:
        _connected_mode()


if __name__ == "__main__":
    main()