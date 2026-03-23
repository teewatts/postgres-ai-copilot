import json
from pathlib import Path

from app.schemas.input import ManualAnalysisInput
from app.schemas.output import (
    AnalysisOutput,
    BottleneckCategory,
    BottleneckSummary,
    ConfidenceLevel,
    PriorityLevel,
    Recommendation,
    RecommendationType,
)


def test_manual_analysis_input_fixture_loads() -> None:
    fixture_path = Path("tests/fixtures/cases/slow_seq_scan_case.json")
    payload = json.loads(fixture_path.read_text())

    analysis_input = ManualAnalysisInput(**payload["input"])

    assert analysis_input.mode.value == "manual"
    assert "SELECT id, email, created_at FROM users" in analysis_input.sql_query
    assert analysis_input.explain_format.value == "text"


def test_analysis_output_schema_can_be_constructed() -> None:
    output = AnalysisOutput(
        summary="Query performs a sequential scan on users for a selective email predicate.",
        confidence=ConfidenceLevel.HIGH,
        primary_bottleneck=BottleneckSummary(
            category=BottleneckCategory.SCAN,
            evidence=[
                "Plan shows Seq Scan on users",
                "Rows Removed by Filter is very high"
            ],
        ),
        recommendations=[
            Recommendation(
                type=RecommendationType.INDEX,
                priority=PriorityLevel.HIGH,
                action="Create an index on users(email).",
                rationale="The predicate filters on email and the current plan scans nearly the entire table.",
                risk="Additional write overhead and index storage cost.",
                sql_candidate="CREATE INDEX CONCURRENTLY idx_users_email ON users (email);",
            )
        ],
        verification_steps=[
            "Run EXPLAIN ANALYZE again after creating the index.",
            "Confirm the planner switches to an Index Scan or Index Only Scan if appropriate."
        ],
        do_not_do=[
            "Do not assume the same index is beneficial if email has very low selectivity across workloads."
        ],
    )

    assert output.primary_bottleneck.category == BottleneckCategory.SCAN
    assert output.recommendations[0].type == RecommendationType.INDEX