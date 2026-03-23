"""
Tests for text-plan parsing.

These tests protect the parser contract for the initial fixture-driven MVP.
They ensure that key plan fields are extracted consistently from the sample
EXPLAIN ANALYZE text case.
"""

import json
from pathlib import Path

from app.parsers.explain_text_parser import parse_explain_text


def test_parse_explain_text_for_seq_scan_case() -> None:
    """Ensure the parser extracts the expected fields from the seq-scan fixture."""
    fixture_path = Path("tests/fixtures/cases/slow_seq_scan_case.json")
    payload = json.loads(fixture_path.read_text())

    plan_text = payload["input"]["explain_plan"]
    parsed = parse_explain_text(plan_text)

    assert parsed.format == "text"
    assert parsed.root_node is not None
    assert parsed.root_node.node_type == "Seq Scan"
    assert parsed.root_node.relation_name == "users"
    assert parsed.root_node.plan_rows == 1.0
    assert parsed.root_node.actual_rows == 1.0
    assert parsed.root_node.rows_removed_by_filter == 999999.0
    assert parsed.execution_time_ms == 412.410
    assert parsed.planning_time_ms == 0.250
    assert parsed.root_node.filter_condition is not None
    assert "email" in parsed.root_node.filter_condition.lower()