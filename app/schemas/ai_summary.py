"""
Schemas for AI-generated explanation output.

These models define the structured response returned by the first AI layer.
The deterministic analysis engine remains the source of truth, while the AI
layer explains and summarizes those findings in a more polished format.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AISummaryOutput(BaseModel):
    """Structured explanation returned by the AI summary workflow."""

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