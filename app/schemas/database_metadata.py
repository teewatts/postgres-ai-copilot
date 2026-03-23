"""
Internal schemas for database metadata used during connected-mode analysis.

These models represent table, column, and index metadata fetched from
PostgreSQL. The analysis pipeline uses this information to improve the
quality of recommendations and avoid suggesting redundant indexes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ColumnMetadata(BaseModel):
    """Represents a single database column used in connected-mode analysis."""

    table_schema: str
    table_name: str
    column_name: str
    data_type: str
    is_nullable: bool


class IndexMetadata(BaseModel):
    """Represents a single index definition for a table."""

    schemaname: str
    tablename: str
    indexname: str
    indexdef: str


class TableMetadata(BaseModel):
    """Groups columns and indexes for a specific table."""

    table_schema: str
    table_name: str
    columns: list[ColumnMetadata] = Field(default_factory=list)
    indexes: list[IndexMetadata] = Field(default_factory=list)