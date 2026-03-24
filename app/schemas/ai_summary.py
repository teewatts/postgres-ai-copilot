"""
Schemas for AI-generated explanation output.

These models define the structured responses returned by the AI layer.
The deterministic analysis engine remains the source of truth, while the AI
layer explains and summarizes those findings in a more polished format.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AISummaryOutput(BaseModel):
    """Structured explanation returned by the single-result AI summary workflow."""

    executive_summary: str = Field(
        ...,
        description="Short high-level explanation of the overall finding.",
    )
    technical_explanation: str = Field(
        ...,
        description="Technical explanation of what the plan shows and why it matters.",
    )
    remediation_summary: str = Field(
        ...,
        description="Summary of the recommended action or why no new action is needed.",
    )
    risk_summary: str = Field(
        ...,
        description="Short explanation of risks or caveats associated with the recommendation.",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Concrete follow-up steps for the user.",
    )


class AIComparisonSummaryOutput(BaseModel):
    """Structured explanation returned by the before/after AI comparison workflow."""

    executive_summary: str = Field(
        ...,
        description="High-level summary of what changed between the before and after states.",
    )
    technical_delta: str = Field(
        ...,
        description="Technical explanation of the plan and evidence differences.",
    )
    recommendation_change: str = Field(
        ...,
        description="Explanation of how and why the recommendation changed.",
    )
    validation_summary: str = Field(
        ...,
        description="Short summary of what should still be validated after the change.",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Concrete follow-up steps based on the comparison.",
    )