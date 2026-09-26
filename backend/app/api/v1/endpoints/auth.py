from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_user_by_id

router = APIRouter()


class GuestLoginRequest(BaseModel):
    role: Literal["senior", "trainee"] = "senior"


@router.post("/guest-login")
async def guest_login(payload: GuestLoginRequest):
    user_id = "u-trainee-02" if payload.role == "trainee" else "u-senior-01"
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    token = f"vsm-session-{user_id}"
    return {
        "token": token,
        "user": user,
    }
