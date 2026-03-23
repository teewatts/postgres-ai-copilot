"""
Tests for connected-mode analysis.

These tests verify that the connected workflow uses the PostgreSQL client,
fetches metadata, and reuses the existing heuristic pipeline correctly.
"""

from app.schemas.database_metadata import IndexMetadata, TableMetadata
from app.schemas.input import ConnectedAnalysisInput, ConnectionSettings
from app.services.analyze_query import analyze_connected_query


def test_analyze_connected_query_recommends_investigation_when_predicate_index_exists(monkeypatch) -> None:
    """Ensure connected analysis avoids a redundant index recommendation when a predicate index exists but is not used."""
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

    def fake_get_table_metadata(database_url: str, table_schema: str, table_name: str) -> TableMetadata:
        return TableMetadata(
            table_schema="public",
            table_name="users",
            columns=[],
            indexes=[
                IndexMetadata(
                    schemaname="public",
                    tablename="users",
                    indexname="idx_users_email",
                    indexdef="CREATE INDEX idx_users_email ON public.users USING btree (email)",
                )
            ],
        )

    monkeypatch.setattr(
        "app.services.analyze_query.get_explain_json",
        fake_get_explain_json,
    )
    monkeypatch.setattr(
        "app.services.analyze_query.get_table_metadata",
        fake_get_table_metadata,
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

    assert result.primary_bottleneck.category.value == "seq_scan"
    assert len(result.recommendations) >= 1
    assert result.recommendations[0].type.value == "investigate"

    rationale = result.recommendations[0].rationale.lower()
    assert "index" in rationale
    assert "already exists" in rationale
    assert "email" in rationale


def test_analyze_connected_query_does_not_recommend_new_index_when_plan_already_uses_predicate_index(monkeypatch) -> None:
    """Ensure connected analysis does not recommend a new index when the plan already uses the predicate column index."""
    sample_plan_json = """
    [
      {
        "Plan": {
          "Node Type": "Index Scan",
          "Index Name": "idx_users_email",
          "Relation Name": "users",
          "Alias": "users",
          "Startup Cost": 0.42,
          "Total Cost": 8.44,
          "Plan Rows": 1,
          "Plan Width": 38,
          "Index Cond": "(email = 'alice@example.com'::text)"
        }
      }
    ]
    """

    def fake_get_explain_json(database_url: str, sql_query: str, statement_timeout_ms: int = 5000) -> str:
        return sample_plan_json

    def fake_get_table_metadata(database_url: str, table_schema: str, table_name: str) -> TableMetadata:
        return TableMetadata(
            table_schema="public",
            table_name="users",
            columns=[],
            indexes=[
                IndexMetadata(
                    schemaname="public",
                    tablename="users",
                    indexname="idx_users_email",
                    indexdef="CREATE INDEX idx_users_email ON public.users USING btree (email)",
                )
            ],
        )

    monkeypatch.setattr(
        "app.services.analyze_query.get_explain_json",
        fake_get_explain_json,
    )
    monkeypatch.setattr(
        "app.services.analyze_query.get_table_metadata",
        fake_get_table_metadata,
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

    assert result.primary_bottleneck.category.value == "index_scan"
    assert len(result.recommendations) >= 1
    assert result.recommendations[0].type.value == "investigate"

    action = result.recommendations[0].action.lower()
    rationale = result.recommendations[0].rationale.lower()

    assert "no new email index recommendation is needed" in action
    assert "already uses an index condition on email" in rationale