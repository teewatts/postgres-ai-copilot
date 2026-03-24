"""
Tests for AI prompt builders.

These tests verify that the prompt-building layer includes the core
deterministic inputs needed by the AI summary workflows.
"""

from app.llm.prompts import build_ai_comparison_prompt, build_ai_summary_prompt
from app.schemas.output import (
    AnalysisOutput,
    BottleneckCategory,
    BottleneckSummary,
    ConfidenceLevel,
    PriorityLevel,
    Recommendation,
    RecommendationType,
)


def _make_sample_result(category: BottleneckCategory, summary: str, action: str) -> AnalysisOutput:
    """Create a representative deterministic analysis result for prompt tests."""
    return AnalysisOutput(
        summary=summary,
        confidence=ConfidenceLevel.HIGH,
        primary_bottleneck=BottleneckSummary(
            category=category,
            evidence=[
                "Plan shows Seq Scan on users.",
                "Filter condition detected: (email = 'alice@example.com'::text)",
                "Inferred predicate column: email",
            ],
        ),
        recommendations=[
            Recommendation(
                type=RecommendationType.INDEX,
                priority=PriorityLevel.HIGH,
                action=action,
                rationale="The query filters on email and the plan indicates a sequential scan.",
                risk="Additional storage and write overhead.",
                sql_candidate="CREATE INDEX CONCURRENTLY idx_users_email ON users (email);",
            )
        ],
        verification_steps=["Re-run EXPLAIN after the change."],
        do_not_do=["Do not apply index recommendations blindly."],
    )


def test_build_ai_summary_prompt_contains_deterministic_context() -> None:
    """Ensure the single-result prompt includes the query and deterministic analysis payload."""
    result = _make_sample_result(
        category=BottleneckCategory.SEQ_SCAN,
        summary="The query appears to rely on a sequential scan.",
        action="Consider adding an index on users(email).",
    )

    prompt = build_ai_summary_prompt(
        sql_query="SELECT * FROM users WHERE email = 'alice@example.com';",
        analysis_result=result,
    )

    assert "SQL Query:" in prompt
    assert "Deterministic Analysis Result:" in prompt
    assert "sequential scan" in prompt.lower()
    assert "users(email)" in prompt.lower()


def test_build_ai_comparison_prompt_contains_before_and_after_context() -> None:
    """Ensure the comparison prompt includes both before and after deterministic payloads."""
    before_result = _make_sample_result(
        category=BottleneckCategory.SEQ_SCAN,
        summary="The query appears to rely on a sequential scan.",
        action="Consider adding an index on users(email).",
    )
    after_result = _make_sample_result(
        category=BottleneckCategory.INDEX_SCAN,
        summary="The query is already using an index-based access path.",
        action="No new email index recommendation is needed for this query.",
    )

    prompt = build_ai_comparison_prompt(
        sql_query="SELECT * FROM users WHERE email = 'alice@example.com';",
        before_result=before_result,
        after_result=after_result,
    )

    assert "Before Deterministic Analysis Result:" in prompt
    assert "After Deterministic Analysis Result:" in prompt
    assert "no new email index recommendation is needed" in prompt.lower()
    assert "index-based access path" in prompt.lower()