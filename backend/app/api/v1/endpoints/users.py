from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Query
from app.core.database import get_user_by_id, get_user_achievements

router = APIRouter()


@router.get("/me")
async def get_current_user(
    user_id: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    target_id = user_id or x_user_id
    if not target_id and authorization:
        # Извлекаем ID из токена vsm-session-<id>
        token_str = authorization.replace("Bearer ", "").strip()
        if token_str.startswith("vsm-session-"):
            target_id = token_str.replace("vsm-session-", "")
        else:
            target_id = token_str

    if not target_id:
        target_id = "u-senior-01"

    user = await get_user_by_id(target_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return user


@router.get("/{user_id}/lms-report")
async def get_lms_employee_report(user_id: str):
    """
    Официальный эндпоинт интеграции с HR/LMS системами ОАО «РЖД».
    Возвращает матрицу квалификации ЗУН, допуск к скоростным линиям и план переобучения.
    """
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    achievements = await get_user_achievements(user_id)
    
    # Расчет индекса квалификации
    skills = [user["service_psychology"], user["safety_tech"], user["routine_discipline"], user["first_aid"]]
    readiness = round(sum(skills) / len(skills))

    # Определение слабой зоны
    skill_map = {
        "Доврачебная помощь": user["first_aid"],
        "График и регламент": user["routine_discipline"],
        "Сервис и психология": user["service_psychology"],
        "Техногенная безопасность": user["safety_tech"]
    }
    weakest = min(skill_map.items(), key=lambda x: x[1])

    return {
        "employee": {
            "id": user["id"],
            "full_name": user["username"],
            "role": user["role"],
            "badge": user["badge"],
            "shifts_completed": user["shifts_count"]
        },
        "qualification": {
            "overall_index": readiness,
            "safety_rating": user.get("safety_tech", 100),
            "loyalty_rating": user["loyalty_score"],
            "status": "Допущен к рейсам ВСМ (Бизнес/Комфорт)" if readiness >= 75 else "Требуется стажировка под контролем шефа поезда"
        },
        "competencies_matrix": skill_map,
        "recommendation": {
            "weak_area": weakest[0],
            "score": weakest[1],
            "action_plan": f"Назначить интерактивный микро-курс по теме '{weakest[0]}' согласно СТО РЖД 03.011"
        },
        "achievements_count": len(achievements),
        "achievements": achievements,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/{user_id}/achievements")
async def get_my_achievements(user_id: str):
    return await get_user_achievements(user_id)

