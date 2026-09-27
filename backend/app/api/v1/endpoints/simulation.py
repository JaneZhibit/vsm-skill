from fastapi import APIRouter
from .sim_state import router as state_router
from .sim_actions import router as actions_router
from .sim_events import router as events_router, LIVE_SCENARIOS_DB

router = APIRouter()
router.include_router(state_router)
router.include_router(actions_router)
router.include_router(events_router)

__all__ = ["router", "LIVE_SCENARIOS_DB"]
