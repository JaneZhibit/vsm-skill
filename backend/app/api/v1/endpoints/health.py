from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Returns operational status and application name for monitoring.",
)
async def get_health() -> HealthResponse:
    """Async health check returning service status."""
    return HealthResponse(
        status="ok",
        app=settings.PROJECT_NAME,
    )
