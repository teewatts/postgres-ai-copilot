"""
Prompt builders for the AI explanation layer.

These helpers convert deterministic analysis results into grounded prompts
for the local LLM. The goal is to keep the model focused on explaining
existing findings rather than inventing new database facts.
"""

from __future__ import annotations

import json

from app.schemas.ai_summary import AIComparisonSummaryOutput, AISummaryOutput


def build_ai_summary_prompt(sql_query: str, analysis_result) -> str:
    """
    Build a grounded prompt for the single-result AI explanation layer.

    Args:
        sql_query: The SQL query being analyzed.
        analysis_result: The deterministic AnalysisOutput object.

    Returns:
        A prompt string instructing the model to explain the deterministic
        findings in a structured, DBA-friendly way.
    """
    analysis_json = analysis_result.model_dump_json(indent=2)
    schema_json = json.dumps(AISummaryOutput.model_json_schema(), indent=2)

    return f"""
You are a PostgreSQL query tuning assistant.

Your job is to explain the deterministic analysis results below.
Do not invent new facts. Do not contradict the supplied findings.
Do not claim measured performance improvements unless they are explicitly present.
If a recommendation says no new index is needed, explain why that is the case.

Return valid JSON matching this schema:
{schema_json}

SQL Query:
{sql_query}

Deterministic Analysis Result:
{analysis_json}
""".strip()


def build_ai_comparison_prompt(
    sql_query: str,
    before_result,
    after_result,
) -> str:
    """
    Build a grounded prompt for the before/after AI comparison workflow.

    Args:
        sql_query: The SQL query analyzed in both snapshots.
        before_result: Deterministic AnalysisOutput for the before snapshot.
        after_result: Deterministic AnalysisOutput for the after snapshot.

    Returns:
        A prompt string instructing the model to explain the comparison in a
        structured, DBA-friendly way.
    """
    before_json = before_result.model_dump_json(indent=2)
    after_json = after_result.model_dump_json(indent=2)
    schema_json = json.dumps(AIComparisonSummaryOutput.model_json_schema(), indent=2)

    return f"""
You are a PostgreSQL query tuning assistant.

Your job is to compare the deterministic before and after analysis results below.
Do not invent new facts. Do not contradict the supplied findings.
Do not claim measured performance improvements unless they are explicitly present.
Explain what changed, why the recommendation changed, and what should still be validated.

Return valid JSON matching this schema:
{schema_json}

SQL Query:
{sql_query}

Before Deterministic Analysis Result:
{before_json}

After Deterministic Analysis Result:
{after_json}
""".strip()