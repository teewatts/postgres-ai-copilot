"""
Tests for connected-mode analysis.

These tests verify that the connected workflow uses the PostgreSQL client
and reuses the existing heuristic pipeline correctly.
"""

from app.schemas.input import ConnectedAnalysisInput, ConnectionSettings
from app.services.analyze_query import analyze_connected_query


def test_analyze_connected_query_uses_live_plan(monkeypatch) -> None:
    """Ensure connected analysis uses the fetched JSON plan and returns a scan finding."""
    sample_plan_json = """
    [
      {
        "Plan": {
          "Node Type": "Seq Scan",
          "Relation Name": "users",
          "Alias": "users",
          "Startup Cost": 0.0,
          "Total Cost": 18342.0,
          "Plan Rows": 1,
          "Plan Width": 48,
          "Actual Startup Time": 0.12,
          "Actual Total Time": 412.345,
          "Actual Rows": 1,
          "Actual Loops": 1,
          "Filter": "((email)::text = 'alice@example.com'::text)",
          "Rows Removed by Filter": 999999
        },
        "Planning Time": 0.25,
        "Execution Time": 412.41
      }
    ]
    """

    def fake_get_explain_json(database_url: str, sql_query: str, statement_timeout_ms: int = 5000) -> str:
        return sample_plan_json

    monkeypatch.setattr(
        "app.services.analyze_query.get_explain_json",
        fake_get_explain_json,
    )

    payload = ConnectedAnalysisInput(
        mode="connected",
        sql_query="SELECT id, email, created_at FROM users WHERE email = 'alice@example.com';",
        connection=ConnectionSettings(
            database_url="postgresql://demo:demo@localhost:5432/demo_db",
            statement_timeout_ms=5000,
        ),
    )

    result = analyze_connected_query(payload)

    assert result.primary_bottleneck.category.value == "scan"
    assert len(result.recommendations) >= 1
    assert result.recommendations[0].type.value == "index"
    assert "email" in result.recommendations[0].action.lower()