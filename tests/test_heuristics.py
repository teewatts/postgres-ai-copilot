"""
Tests for service-layer heuristic analysis.

These tests verify that the manual analysis workflow produces the expected
bottleneck classification and recommendation signals for the initial fixture.
"""

import json
from pathlib import Path

from app.schemas.input import ManualAnalysisInput
from app.services.analyze_query import analyze_manual_query


def test_analyze_manual_query_recommends_email_index_for_seq_scan_case() -> None:
    """Ensure the service recommends an email index for the sample seq-scan case."""
    fixture_path = Path("tests/fixtures/cases/slow_seq_scan_case.json")
    payload = json.loads(fixture_path.read_text())

    analysis_input = ManualAnalysisInput(**payload["input"])
    result = analyze_manual_query(analysis_input)

    assert result.primary_bottleneck.category.value == "seq_scan"
    assert len(result.recommendations) >= 1
    assert result.recommendations[0].type.value == "index"
    assert "email" in result.recommendations[0].action.lower()
    assert result.confidence.value in {"medium", "high"}