"""
Tests for EXPLAIN plan parsing.

These tests protect the parser contract for the initial fixture-driven MVP.
They ensure that both text and JSON execution-plan inputs are normalized
correctly into the internal plan schema.
"""

from pathlib import Path

from app.parsers.explain_json_parser import parse_explain_json
from app.parsers.explain_text_parser import parse_explain_text


def test_parse_explain_text_for_seq_scan_case() -> None:
    """Ensure the text parser extracts the expected fields from the seq-scan fixture."""
    fixture_path = Path("tests/fixtures/cases/slow_seq_scan_case.json")
    plan_text = fixture_path.read_text()

    # The case fixture is stored as a JSON document, so we parse it as text here
    # and then extract the nested EXPLAIN text payload for the parser test.
    import json

    payload = json.loads(plan_text)
    parsed = parse_explain_text(payload["input"]["explain_plan"])

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


def test_parse_explain_json_for_seq_scan_case() -> None:
    """Ensure the JSON parser extracts the expected fields from the sample plan."""
    fixture_path = Path("tests/fixtures/plans/slow_seq_scan_plan.json")
    plan_json = fixture_path.read_text()

    parsed = parse_explain_json(plan_json)

    assert parsed.format == "json"
    assert parsed.root_node is not None
    assert parsed.root_node.node_type == "Seq Scan"
    assert parsed.root_node.relation_name == "users"
    assert parsed.root_node.plan_rows == 1
    assert parsed.root_node.actual_rows == 1
    assert parsed.root_node.rows_removed_by_filter == 999999
    assert parsed.execution_time_ms == 412.41
    assert parsed.planning_time_ms == 0.25
    assert parsed.root_node.filter_condition is not None
    assert "email" in parsed.root_node.filter_condition.lower()