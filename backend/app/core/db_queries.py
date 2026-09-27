import aiosqlite
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.db_setup import DB_PATH
from app.core.db_seeds import ACHIEVEMENTS_CATALOG

def compute_Composite_score(u: Dict[str, Any]) -> int:
    """
    Комплексный расчет рейтинга для лидерборда:
    - База: Лояльность (30%) + Безопасность (30%)
    - Опыт: +8 очков за каждый решенный инцидент
    - Точность решений: до +50 очков за % правильных ответов
    - Ежедневная активность (streak): +10 очков за каждый день подряд
    """
    loyalty = u.get("loyalty_score", 80)
    safety = u.get("safety_tech", 80)
    resolved = u.get("incidents_resolved", 0)
    correct = u.get("correct_decisions", 0)
    streak = u.get("streak_days", 1)

    accuracy_ratio = (correct / resolved) if resolved > 0 else 0.5
    base_points = (loyalty * 0.3) + (safety * 0.3)
    experience_points = resolved * 8
    accuracy_points = accuracy_ratio * 50
    streak_points = streak * 10

    return round(base_points + experience_points + accuracy_points + streak_points)


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            user_dict = dict(row)
            user_dict["rating_score"] = compute_Composite_score(user_dict)
            resolved = user_dict.get("incidents_resolved", 0)
            correct = user_dict.get("correct_decisions", 0)
            user_dict["accuracy_percent"] = round((correct / resolved) * 100) if resolved > 0 else 100
            return user_dict


async def get_leaderboard() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            users = []
            for r in rows:
                d = dict(r)
                d["rating_score"] = compute_Composite_score(d)
                resolved = d.get("incidents_resolved", 0)
                correct = d.get("correct_decisions", 0)
                d["accuracy_percent"] = round((correct / resolved) * 100) if resolved > 0 else 100
                users.append(d)
            users.sort(key=lambda x: x["rating_score"], reverse=True)
            return users


async def log_action(
    user_id: str,
    incident_id: str,
    option_id: str,
    loyalty_delta: int,
    safety_delta: int = 0,
    feedback: str = "",
) -> Optional[Dict[str, Any]]:
    """Логирует действие, обновляет статистику в БД и проверяет открытие новых достижений."""
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row

        async with conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            user_row = await cursor.fetchone()
            if not user_row:
                return None

        now_str = datetime.utcnow().isoformat()
        await conn.execute("""
            INSERT INTO action_logs (user_id, timestamp, incident_id, option_id, loyalty_delta, safety_delta, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, now_str, incident_id, option_id, loyalty_delta, safety_delta, feedback))

        user = dict(user_row)
        is_correct = (loyalty_delta >= 0 and safety_delta >= 0) and (loyalty_delta > 0 or safety_delta > 0)

        new_loyalty = max(0, min(100, user["loyalty_score"] + loyalty_delta))
        new_safety = max(0, min(100, user["safety_tech"] + safety_delta))
        new_resolved = user.get("incidents_resolved", 0) + 1
        new_correct = user.get("correct_decisions", 0) + (1 if is_correct else 0)

        new_service = user["service_psychology"]
        new_discipline = user["routine_discipline"]
        new_first_aid = user["first_aid"]

        if is_correct:
            new_service = min(100, new_service + 4)
            new_discipline = min(100, new_discipline + 3)
        else:
            new_service = max(20, new_service - 2)

        if any(kw in incident_id for kw in ["air", "temp", "vent", "climate", "vape", "bag", "luggage"]):
            new_safety = min(100, new_safety + (3 if is_correct else 0))
        if any(kw in incident_id for kw in ["med", "help", "doctor", "pills", "kinetosis"]):
            new_first_aid = min(100, new_first_aid + (5 if is_correct else 0))

        await conn.execute("""
            UPDATE users
            SET loyalty_score = ?,
                safety_tech = ?,
                service_psychology = ?,
                routine_discipline = ?,
                first_aid = ?,
                incidents_resolved = ?,
                correct_decisions = ?
            WHERE id = ?
        """, (
            new_loyalty, new_safety, new_service, new_discipline,
            new_first_aid, new_resolved, new_correct, user_id
        ))
        await conn.commit()

    # Проверяем и выдаем ачивки (возвращаем список только что открытых!)
    newly_unlocked: List[Dict[str, Any]] = []

    if is_correct:
        if any(kw in incident_id for kw in ["vape", "bag", "smoke", "luggage"]):
            ach = await unlock_achievement(user_id, "safety_first")
            if ach:
                newly_unlocked.append(ach)
        if any(kw in incident_id for kw in ["kinetosis", "med", "pills"]):
            ach = await unlock_achievement(user_id, "med_hero")
            if ach:
                newly_unlocked.append(ach)
        if new_correct >= 5 or incident_id == "inc_med_pills_01":
            ach = await unlock_achievement(user_id, "sto_expert")
            if ach:
                newly_unlocked.append(ach)
        if "help" in option_id or "chief" in option_id or "medic" in option_id:
            ach = await unlock_achievement(user_id, "team_player")
            if ach:
                newly_unlocked.append(ach)

    updated = await get_user_by_id(user_id)
    if updated:
        updated["new_achievements"] = newly_unlocked
    return updated


async def unlock_achievement(user_id: str, code: str) -> Optional[Dict[str, Any]]:
    if code not in ACHIEVEMENTS_CATALOG:
        return None
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT id FROM user_achievements WHERE user_id = ? AND code = ?",
            (user_id, code),
        ) as c:
            if await c.fetchone():
                return None

        info = ACHIEVEMENTS_CATALOG[code]
        now_str = datetime.utcnow().isoformat()
        await conn.execute("""
            INSERT INTO user_achievements (user_id, code, title, description, icon, unlocked_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, code, info["title"], info["description"], info["icon"], now_str))
        await conn.commit()
        return {"code": code, **info, "unlocked_at": now_str}


async def get_user_achievements(user_id: str) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT * FROM user_achievements WHERE user_id = ? ORDER BY id ASC",
            (user_id,),
        ) as c:
            rows = await c.fetchall()
            return [dict(r) for r in rows]
