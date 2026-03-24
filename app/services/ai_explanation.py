"""
Service-layer AI explanation workflow.

This module generates grounded AI explanations from deterministic analysis
results. The deterministic engine remains authoritative, while the AI layer
adds clearer narrative and DBA-style communication.
"""

from __future__ import annotations

from app.llm.client import generate_structured_ai_summary
from app.llm.prompts import build_ai_summary_prompt
from app.schemas.ai_summary import AISummaryOutput


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