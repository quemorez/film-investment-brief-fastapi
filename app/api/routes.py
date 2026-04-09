from fastapi import APIRouter
from app.models.schemas import BriefingRequest, BriefingResponse
from app.services.briefing_engine import generate_briefing_payload

router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True, "service": "film-investment-brief-api"}

@router.post("/generate", response_model=BriefingResponse)
def generate_briefing(req: BriefingRequest):
    return generate_briefing_payload(req)
