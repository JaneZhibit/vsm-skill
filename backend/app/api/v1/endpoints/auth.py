from typing import Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_user_by_id

router = APIRouter()


class GuestLoginRequest(BaseModel):
    role: Literal["senior", "trainee", "chief"] = "senior"
    gender: Literal["m", "f"] = "m"
    user_id: Optional[str] = None


ROLE_GENDER_TO_USER_ID = {
    ("senior", "m"): "u-senior-01",   # Алексей Смирнов
    ("senior", "f"): "u-anna-04",     # Анна Родионова
    ("trainee", "m"): "u-trainee-02", # Дмитрий Волков
    ("trainee", "f"): "u-maria-05",   # Мария Соколова
    ("chief", "f"): "u-elena-01",     # Елена Васильева
    ("chief", "m"): "u-senior-01",
}


@router.post("/guest-login")
async def guest_login(payload: GuestLoginRequest):
    target_id = payload.user_id or ROLE_GENDER_TO_USER_ID.get(
        (payload.role, payload.gender), "u-senior-01"
    )
    user = await get_user_by_id(target_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    token = f"vsm-session-{target_id}"
    return {
        "token": token,
        "user": user,
    }
