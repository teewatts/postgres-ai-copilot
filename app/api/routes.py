from fastapi import APIRouter

from app.schemas.input import ManualAnalysisInput
from app.schemas.output import AnalysisOutput
from app.services.analyze_query import analyze_manual_query

router = APIRouter()


@router.post("/analyze", response_model=AnalysisOutput)
def analyze_query(payload: ManualAnalysisInput) -> AnalysisOutput:
    return analyze_manual_query(payload)