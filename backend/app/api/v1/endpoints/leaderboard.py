from fastapi import APIRouter
from app.core.database import get_leaderboard

router = APIRouter()


@router.get("")
@router.get("/")
async def get_current_leaderboard():
    leaderboard = await get_leaderboard()
    return {
        "leaderboard": leaderboard,
        "total": len(leaderboard),
    }
