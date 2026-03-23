from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class InputMode(str, Enum):
    MANUAL = "manual"
    CONNECTED = "connected"


class ExplainFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


class ConnectionSettings(BaseModel):
    database_url: str = Field(..., description="PostgreSQL connection string")
    statement_timeout_ms: int = Field(
        default=5000,
        ge=100,
        le=60000,
        description="Timeout for live analysis queries in milliseconds",
    )
    allow_explain_analyze: bool = Field(
        default=False,
        description="Whether EXPLAIN ANALYZE is allowed in connected mode",
    )
    allow_non_select: bool = Field(
        default=False,
        description="Whether non-SELECT statements are allowed for analysis",
    )


class ManualAnalysisInput(BaseModel):
    mode: Literal[InputMode.MANUAL] = InputMode.MANUAL
    sql_query: str = Field(..., min_length=1, description="SQL query to analyze")
    explain_plan: str | None = Field(
        default=None,
        description="Optional EXPLAIN or EXPLAIN ANALYZE output",
    )
    explain_format: ExplainFormat | None = Field(
        default=None,
        description="Format of the supplied plan if provided",
    )
    schema_ddl: str | None = Field(
        default=None,
        description="Optional schema DDL for relevant tables",
    )
    index_definitions: str | None = Field(
        default=None,
        description="Optional CREATE INDEX statements or index metadata",
    )
    notes: str | None = Field(
        default=None,
        description="Optional analyst notes or context",
    )


class ConnectedAnalysisInput(BaseModel):
    mode: Literal[InputMode.CONNECTED] = InputMode.CONNECTED
    sql_query: str = Field(..., min_length=1, description="SQL query to analyze")
    connection: ConnectionSettings
    schema_allowlist: list[str] | None = Field(
        default=None,
        description="Optional schemas allowed for introspection",
    )
    table_allowlist: list[str] | None = Field(
        default=None,
        description="Optional tables allowed for introspection",
    )


AnalysisInput = ManualAnalysisInput | ConnectedAnalysisInput