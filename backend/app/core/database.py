import os
import aiosqlite
from datetime import datetime
from typing import Any, Dict, List, Optional

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
DB_PATH = os.getenv("VSM_DB_PATH", str(BACKEND_DIR / "vsm.db"))

INITIAL_SEED_USERS = [
    {
        "id": "u-elena-01",
        "username": "Елена Васильева",
        "gender": "f",
        "role": "Шеф поездной бригады",
        "badge": "ВСМ-1 • Премиум",
        "shifts_count": 32,
        "service_psychology": 98,
        "safety_tech": 100,
        "routine_discipline": 95,
        "first_aid": 90,
        "loyalty_score": 98,
        "incidents_resolved": 48,
        "correct_decisions": 46,
        "streak_days": 7,
    },
    {
        "id": "u-senior-01",
        "username": "Алексей Смирнов",
        "gender": "m",
        "role": "Старший проводник",
        "badge": "ВСМ-1 • Бизнес-класс",
        "shifts_count": 14,
        "service_psychology": 85,
        "safety_tech": 100,
        "routine_discipline": 65,
        "first_aid": 40,
        "loyalty_score": 85,
        "incidents_resolved": 22,
        "correct_decisions": 18,
        "streak_days": 4,
    },
    {
        "id": "u-anna-04",
        "username": "Анна Родионова",
        "gender": "f",
        "role": "Старший проводник",
        "badge": "ВСМ-1 • Бизнес-класс",
        "shifts_count": 12,
        "service_psychology": 88,
        "safety_tech": 92,
        "routine_discipline": 80,
        "first_aid": 55,
        "loyalty_score": 86,
        "incidents_resolved": 19,
        "correct_decisions": 16,
        "streak_days": 5,
    },
    {
        "id": "u-trainee-02",
        "username": "Дмитрий Волков",
        "gender": "m",
        "role": "Проводник-стажер",
        "badge": "ВСМ-1 • Стажер",
        "shifts_count": 2,
        "service_psychology": 45,
        "safety_tech": 50,
        "routine_discipline": 40,
        "first_aid": 35,
        "loyalty_score": 62,
        "incidents_resolved": 4,
        "correct_decisions": 2,
        "streak_days": 1,
    },
    {
        "id": "u-maria-05",
        "username": "Мария Соколова",
        "gender": "f",
        "role": "Проводник-стажер",
        "badge": "ВСМ-1 • Стажер",
        "shifts_count": 3,
        "service_psychology": 55,
        "safety_tech": 60,
        "routine_discipline": 50,
        "first_aid": 40,
        "loyalty_score": 68,
        "incidents_resolved": 5,
        "correct_decisions": 4,
        "streak_days": 2,
    },
]

ACHIEVEMENTS_CATALOG = {
    "first_trip": {
        "title": "Первый рейс ВСМ",
        "description": "Успешно начать и пройти смену на высокоскоростной магистрали",
        "icon": "🚄",
    },
    "safety_first": {
        "title": "Страж безопасности",
        "description": "Безупречно пресечь нарушение пожарной или транспортной безопасности",
        "icon": "🛡️",
    },
    "med_hero": {
        "title": "Скорая помощь 400 км/ч",
        "description": "Грамотно оказать помощь пассажиру при медицинском инциденте",
        "icon": "🩺",
    },
    "sto_expert": {
        "title": "Знаток СТО РЖД",
        "description": "Принять 5 верных решений подряд строго по регламенту ВСМ",
        "icon": "📜",
    },
    "team_player": {
        "title": "Командная работа",
        "description": "Привлечь начальника поезда или пассажиров для решения сложной ситуации",
        "icon": "🤝",
    },
}


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


async def init_db() -> None:
    """Асинхронная инициализация таблиц, мягкие миграции и сидинг."""
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                gender TEXT DEFAULT 'm',
                role TEXT NOT NULL,
                badge TEXT NOT NULL,
                shifts_count INTEGER DEFAULT 0,
                service_psychology INTEGER DEFAULT 85,
                safety_tech INTEGER DEFAULT 100,
                routine_discipline INTEGER DEFAULT 65,
                first_aid INTEGER DEFAULT 40,
                loyalty_score INTEGER DEFAULT 85,
                incidents_resolved INTEGER DEFAULT 0,
                correct_decisions INTEGER DEFAULT 0,
                streak_days INTEGER DEFAULT 1
            )
        """)

        # Мягкие миграции для существующей локальной БД
        for col_sql in [
            "ALTER TABLE users ADD COLUMN gender TEXT DEFAULT 'm'",
            "ALTER TABLE users ADD COLUMN incidents_resolved INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN correct_decisions INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN streak_days INTEGER DEFAULT 1",
        ]:
            try:
                await conn.execute(col_sql)
            except Exception:
                pass

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                incident_id TEXT NOT NULL,
                option_id TEXT NOT NULL,
                loyalty_delta INTEGER DEFAULT 0,
                safety_delta INTEGER DEFAULT 0,
                feedback TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                code TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                icon TEXT NOT NULL,
                unlocked_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await conn.commit()

        # Сидинг всех демо-пользователей (добавляем недостающих по ID)
        for u in INITIAL_SEED_USERS:
            async with conn.execute("SELECT id FROM users WHERE id = ?", (u["id"],)) as cur:
                exists = await cur.fetchone()
            if not exists:
                await conn.execute("""
                    INSERT INTO users (
                        id, username, gender, role, badge, shifts_count,
                        service_psychology, safety_tech, routine_discipline, first_aid,
                        loyalty_score, incidents_resolved, correct_decisions, streak_days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    u["id"], u["username"], u["gender"], u["role"], u["badge"], u["shifts_count"],
                    u["service_psychology"], u["safety_tech"], u["routine_discipline"], u["first_aid"],
                    u["loyalty_score"], u["incidents_resolved"], u["correct_decisions"], u["streak_days"]
                ))
            else:
                await conn.execute("""
                    UPDATE users SET
                        gender = ?,
                        role = ?,
                        badge = ?,
                        incidents_resolved = CASE WHEN incidents_resolved = 0 THEN ? ELSE incidents_resolved END,
                        correct_decisions = CASE WHEN correct_decisions = 0 THEN ? ELSE correct_decisions END,
                        streak_days = CASE WHEN streak_days <= 1 THEN ? ELSE streak_days END
                    WHERE id = ?
                """, (
                    u["gender"], u["role"], u["badge"],
                    u["incidents_resolved"], u["correct_decisions"], u["streak_days"],
                    u["id"]
                ))
        await conn.commit()


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
