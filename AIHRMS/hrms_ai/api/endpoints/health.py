"""
Health check endpoints
"""
from datetime import datetime
from fastapi import APIRouter
from models.schemas import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="AI HRMS Backend is running",
        timestamp=datetime.utcnow().isoformat()
    )