"""
Tests for service-layer heuristic analysis.

These tests verify that the manual analysis workflow produces the expected
bottleneck classification and recommendation signals for the initial fixture.
"""

import json
from pathlib import Path

from app.schemas.input import ManualAnalysisInput
from app.services.analyze_query import analyze_manual_query


def test_analyze_manual_query_recommends_index_for_inferred_predicate_column() -> None:
    """Ensure the service recommends an index using the inferred predicate column."""
    fixture_path = Path("tests/fixtures/cases/slow_seq_scan_case.json")
    payload = json.loads(fixture_path.read_text())

    analysis_input = ManualAnalysisInput(**payload["input"])
    result = analyze_manual_query(analysis_input)

    assert result.primary_bottleneck.category.value == "seq_scan"
    assert len(result.recommendations) >= 1
    assert result.recommendations[0].type.value == "index"
    assert "users(email)" in result.recommendations[0].action.lower()
    assert "idx_users_email" in (result.recommendations[0].sql_candidate or "").lower()
    assert result.confidence.value in {"medium", "high"}