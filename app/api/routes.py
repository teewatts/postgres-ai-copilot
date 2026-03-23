"""
API routes for the Postgres AI Copilot application.

This module defines the external HTTP interface for analysis requests.
Routes should remain thin and delegate business logic to service modules.
"""

from fastapi import APIRouter

from app.schemas.input import ManualAnalysisInput
from app.schemas.output import AnalysisOutput
from app.services.analyze_query import analyze_manual_query

router = APIRouter()


@router.post("/analyze", response_model=AnalysisOutput)
def analyze_query(payload: ManualAnalysisInput) -> AnalysisOutput:
    """
    Analyze a manually supplied SQL query and optional execution-plan context.

    The current version supports the manual-input workflow used by the MVP.
    """
    return analyze_manual_query(payload)