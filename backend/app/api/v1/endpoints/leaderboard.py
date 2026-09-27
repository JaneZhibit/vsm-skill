from fastapi import APIRouter
from app.core.db_queries import get_leaderboard

router = APIRouter()


@router.get("")
@router.get("/")
async def get_current_leaderboard():
    leaderboard = await get_leaderboard()
    return {
        "leaderboard": leaderboard,
        "total": len(leaderboard),
    }
