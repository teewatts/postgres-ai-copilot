"""
Service-layer AI explanation workflows.

This module generates grounded AI explanations from deterministic analysis
results. The deterministic engine remains authoritative, while the AI layer
adds clearer narrative and DBA-style communication.
"""

from __future__ import annotations

from app.llm.client import (
    generate_structured_ai_comparison_summary,
    generate_structured_ai_summary,
)
from app.llm.prompts import build_ai_comparison_prompt, build_ai_summary_prompt
from app.schemas.ai_summary import AIComparisonSummaryOutput, AISummaryOutput


def generate_ai_explanation(
    sql_query: str,
    analysis_result,
    model: str = "llama3.1:8b",
) -> AISummaryOutput:
    """
    Generate a structured AI explanation for a deterministic analysis result.

    Args:
        sql_query: The SQL query being analyzed.
        analysis_result: Deterministic AnalysisOutput from the engine.
        model: Ollama model name.

    Returns:
        A validated structured AI explanation.
    """
    prompt = build_ai_summary_prompt(sql_query=sql_query, analysis_result=analysis_result)
    return generate_structured_ai_summary(prompt=prompt, model=model)


def generate_ai_comparison_explanation(
    sql_query: str,
    before_result,
    after_result,
    model: str = "llama3.1:8b",
) -> AIComparisonSummaryOutput:
    """
    Generate a structured AI explanation for a deterministic before/after comparison.

    Args:
        sql_query: The SQL query being analyzed in both snapshots.
        before_result: Deterministic AnalysisOutput for the before snapshot.
        after_result: Deterministic AnalysisOutput for the after snapshot.
        model: Ollama model name.

    Returns:
        A validated structured AI comparison explanation.
    """
    prompt = build_ai_comparison_prompt(
        sql_query=sql_query,
        before_result=before_result,
        after_result=after_result,
    )
    return generate_structured_ai_comparison_summary(prompt=prompt, model=model)