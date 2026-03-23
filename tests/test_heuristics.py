import json
from pathlib import Path

from app.schemas.input import ManualAnalysisInput
from app.services.analyze_query import analyze_manual_query


def test_analyze_manual_query_recommends_email_index_for_seq_scan_case() -> None:
    fixture_path = Path("tests/fixtures/cases/slow_seq_scan_case.json")
    payload = json.loads(fixture_path.read_text())

    analysis_input = ManualAnalysisInput(**payload["input"])
    result = analyze_manual_query(analysis_input)

    assert result.primary_bottleneck.category.value == "scan"
    assert len(result.recommendations) >= 1
    assert result.recommendations[0].type.value == "index"
    assert "email" in result.recommendations[0].action.lower()
    assert result.confidence.value in {"medium", "high"}