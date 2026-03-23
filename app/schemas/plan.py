from __future__ import annotations

from pydantic import BaseModel, Field


class PlanNode(BaseModel):
    node_type: str = Field(..., description="Plan node type, e.g. Seq Scan, Index Scan, Nested Loop")
    relation_name: str | None = Field(default=None, description="Underlying table or relation name")
    index_name: str | None = Field(default=None, description="Index name when applicable")
    startup_cost: float | None = None
    total_cost: float | None = None
    plan_rows: float | None = None
    actual_rows: float | None = None
    actual_total_time: float | None = None
    filter_condition: str | None = None
    index_condition: str | None = None
    join_filter: str | None = None
    rows_removed_by_filter: float | None = None
    children: list["PlanNode"] = Field(default_factory=list)


class PlanSummary(BaseModel):
    format: str = Field(..., description="Source plan format, e.g. text or json")
    raw_plan: str = Field(..., description="Original plan payload")
    planning_time_ms: float | None = None
    execution_time_ms: float | None = None
    root_node: PlanNode | None = None
    warnings: list[str] = Field(default_factory=list)


PlanNode.model_rebuild()