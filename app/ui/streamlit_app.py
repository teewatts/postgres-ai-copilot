"""
Streamlit UI for Postgres AI Copilot.

This module provides a lightweight interactive interface for the current
analysis workflows. It supports manual analysis, connected analysis,
and a before/after comparison workflow for connected-mode snapshots.
"""

from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

from app.schemas.input import (
    ConnectedAnalysisInput,
    ConnectionSettings,
    ExplainFormat,
    ManualAnalysisInput,
)
from app.services.analyze_query import analyze_connected_query, analyze_manual_query


def _build_database_url(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
) -> str:
    """
    Build a PostgreSQL connection string from individual connection fields.

    Args:
        host: Database host name or IP address.
        port: Database port.
        database: Database name.
        username: Database user name.
        password: Database password.

    Returns:
        A PostgreSQL connection string suitable for psycopg.
    """
    return f"postgresql://{username}:{password}@{host}:{port}/{database}"


def _initialize_session_state() -> None:
    """
    Initialize Streamlit session-state keys used by the comparison workflow.

    Streamlit session state persists values across reruns for a user session,
    which makes it a good fit for storing before/after analysis snapshots.
    """
    if "before_snapshot" not in st.session_state:
        st.session_state.before_snapshot = None

    if "after_snapshot" not in st.session_state:
        st.session_state.after_snapshot = None

    if "last_connected_result" not in st.session_state:
        st.session_state.last_connected_result = None

    if "last_connected_sql" not in st.session_state:
        st.session_state.last_connected_sql = None


def _extract_comparison_fields(result) -> dict[str, str]:
    """
    Extract a compact set of fields for before/after comparison rendering.

    Args:
        result: The AnalysisOutput object returned by the service layer.

    Returns:
        A dictionary of comparison-friendly string values.
    """
    evidence = result.primary_bottleneck.evidence

    filter_condition = next(
        (item.removeprefix("Filter condition detected: ").strip()
         for item in evidence
         if item.startswith("Filter condition detected: ")),
        "N/A",
    )

    index_condition = next(
        (item.removeprefix("Index condition detected: ").strip()
         for item in evidence
         if item.startswith("Index condition detected: ")),
        "N/A",
    )

    predicate_column = next(
        (item.removeprefix("Inferred predicate column: ").strip()
         for item in evidence
         if item.startswith("Inferred predicate column: ")),
        "N/A",
    )

    recommendation_type = (
        result.recommendations[0].type.value if result.recommendations else "none"
    )
    recommendation_action = (
        result.recommendations[0].action if result.recommendations else "No recommendation"
    )

    return {
        "summary": result.summary,
        "category": result.primary_bottleneck.category.value,
        "confidence": result.confidence.value,
        "filter_condition": filter_condition,
        "index_condition": index_condition,
        "predicate_column": predicate_column,
        "recommendation_type": recommendation_type,
        "recommendation_action": recommendation_action,
    }


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
            with st.expander(
                f"{rec.type.value.upper()} | {rec.priority.value.upper()} | {rec.action}"
            ):
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


def _render_snapshot_card(label: str, snapshot: dict | None) -> None:
    """
    Render a saved before/after snapshot.

    Args:
        label: Human-readable label such as 'Before' or 'After'.
        snapshot: Saved snapshot dictionary from session state.
    """
    st.subheader(label)

    if snapshot is None:
        st.info(f"No {label.lower()} snapshot saved yet.")
        return

    st.write(f"**SQL Query:** `{snapshot['sql_query']}`")
    _render_analysis_result(snapshot["result"])


def _render_comparison_view() -> None:
    """
    Render the before/after comparison section when snapshots are available.
    """
    before_snapshot = st.session_state.before_snapshot
    after_snapshot = st.session_state.after_snapshot

    st.header("Before / After Comparison")

    col1, col2 = st.columns(2)

    with col1:
        _render_snapshot_card("Before", before_snapshot)

    with col2:
        _render_snapshot_card("After", after_snapshot)

    if before_snapshot is None or after_snapshot is None:
        st.caption("Save both a Before and an After snapshot to see a comparison summary.")
        return

    before_fields = _extract_comparison_fields(before_snapshot["result"])
    after_fields = _extract_comparison_fields(after_snapshot["result"])

    st.subheader("Comparison Summary")
    st.write(f"- Category: `{before_fields['category']}` → `{after_fields['category']}`")
    st.write(f"- Confidence: `{before_fields['confidence']}` → `{after_fields['confidence']}`")
    st.write(
        f"- Predicate column: `{before_fields['predicate_column']}` → "
        f"`{after_fields['predicate_column']}`"
    )
    st.write(
        f"- Filter condition: `{before_fields['filter_condition']}` → "
        f"`{after_fields['filter_condition']}`"
    )
    st.write(
        f"- Index condition: `{before_fields['index_condition']}` → "
        f"`{after_fields['index_condition']}`"
    )
    st.write(
        f"- Recommendation type: `{before_fields['recommendation_type']}` → "
        f"`{after_fields['recommendation_type']}`"
    )
    st.write(
        f"- Recommendation action: `{before_fields['recommendation_action']}` → "
        f"`{after_fields['recommendation_action']}`"
    )


def _manual_mode() -> None:
    """
    Render the manual analysis workflow.

    This mode accepts pasted SQL and optional EXPLAIN plan content.
    """
    st.header("Manual Analysis")

    with st.form("manual_analysis_form"):
        sql_query = st.text_area(
            "SQL Query",
            height=140,
            value="SELECT id, email, created_at FROM users WHERE email = 'alice@example.com';",
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

        submitted = st.form_submit_button("Run Manual Analysis", type="primary")

    if submitted:
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

    This mode connects to PostgreSQL, fetches a live JSON plan, analyzes it,
    and allows the user to save snapshots for before/after comparison.
    """
    st.header("Connected Analysis")

    with st.form("connected_analysis_form"):
        col1, col2 = st.columns(2)

        with col1:
            host = st.text_input("Host", value="localhost")
            port = st.number_input(
                "Port",
                min_value=1,
                max_value=65535,
                value=5433,
                step=1,
            )
            database = st.text_input("Database", value="postgres_ai_copilot_demo")

        with col2:
            username = st.text_input("Username", value="postgres")
            password = st.text_input("Password", type="password")
            statement_timeout_ms = st.number_input(
                "Statement Timeout (ms)",
                min_value=100,
                max_value=60000,
                value=5000,
                step=100,
            )

        sql_query = st.text_area(
            "SQL Query",
            height=140,
            value="SELECT id, email, created_at FROM users WHERE email = 'alice@example.com';",
        )

        submitted = st.form_submit_button("Run Connected Analysis", type="primary")

    if submitted:
        try:
            database_url = _build_database_url(
                host=host,
                port=int(port),
                database=database,
                username=username,
                password=password,
            )

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

            st.session_state.last_connected_result = result
            st.session_state.last_connected_sql = sql_query

            _render_analysis_result(result)
        except ValidationError as exc:
            st.error("Input validation failed.")
            st.code(str(exc))
        except Exception as exc:
            st.error("Connected analysis failed.")
            st.code(str(exc))

    if st.session_state.last_connected_result is not None:
        st.subheader("Snapshot Controls")

        button_col1, button_col2, button_col3 = st.columns(3)

        with button_col1:
            if st.button("Save Current Result as Before"):
                st.session_state.before_snapshot = {
                    "sql_query": st.session_state.last_connected_sql,
                    "result": st.session_state.last_connected_result,
                }
                st.success("Saved current connected result as Before.")

        with button_col2:
            if st.button("Save Current Result as After"):
                st.session_state.after_snapshot = {
                    "sql_query": st.session_state.last_connected_sql,
                    "result": st.session_state.last_connected_result,
                }
                st.success("Saved current connected result as After.")

        with button_col3:
            if st.button("Clear Comparison Snapshots"):
                st.session_state.before_snapshot = None
                st.session_state.after_snapshot = None
                st.success("Cleared Before and After snapshots.")

        _render_comparison_view()


def main() -> None:
    """
    Run the Streamlit application.
    """
    _initialize_session_state()

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