"""
Input schemas for analysis requests.

These models define the request payloads accepted by the application.
They support both the current manual-input workflow and the future
connected-mode workflow that will analyze queries against a live database.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class InputMode(str, Enum):
    """Supported request modes for the analysis pipeline."""

    MANUAL = "manual"
    CONNECTED = "connected"


class ExplainFormat(str, Enum):
    """Supported formats for supplied execution plans."""

    TEXT = "text"
    JSON = "json"


class ConnectionSettings(BaseModel):
    """Connection settings for future live-database analysis."""

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
    """Payload for the manual analysis workflow used in the MVP."""

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
    """Payload for the future connected workflow against a live database."""

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


# The analysis pipeline will accept either manual input or connected-mode input.
AnalysisInput = ManualAnalysisInput | ConnectedAnalysisInput