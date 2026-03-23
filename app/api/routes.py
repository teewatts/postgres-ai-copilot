"""
API routes for the Postgres AI Copilot application.

This module defines the external HTTP interface for analysis requests.
Routes should remain thin and delegate business logic to service modules.
"""

from fastapi import APIRouter

from app.schemas.input import ConnectedAnalysisInput, ManualAnalysisInput
from app.schemas.output import AnalysisOutput
from app.services.analyze_query import analyze_connected_query, analyze_manual_query

router = APIRouter()


@router.post("/analyze", response_model=AnalysisOutput)
def analyze_query(payload: ManualAnalysisInput) -> AnalysisOutput:
    """
    Analyze a manually supplied SQL query and optional execution-plan context.

    The current manual workflow supports pasted text and JSON EXPLAIN input.
    """
    return analyze_manual_query(payload)


@router.post("/analyze-connected", response_model=AnalysisOutput)
def analyze_connected(payload: ConnectedAnalysisInput) -> AnalysisOutput:
    """
    Analyze a query by fetching its plan directly from PostgreSQL.

    This endpoint is the first connected-mode slice and currently supports
    read-only SELECT analysis through EXPLAIN (FORMAT JSON).
    """
    return analyze_connected_query(payload)