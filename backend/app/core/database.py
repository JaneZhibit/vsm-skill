import os
import aiosqlite
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.getenv("VSM_DB_PATH", "./vsm.db")

INITIAL_SEED_USERS = [
    {
        "id": "u-elena-01",
        "username": "Елена Васильева",
        "role": "Шеф-поездной бригады",
        "badge": "ВСМ-1 • Премиум",
        "shifts_count": 32,
        "service_psychology": 98,
        "safety_tech": 100,
        "routine_discipline": 95,
        "first_aid": 90,
        "loyalty_score": 98,
    },
    {
        "id": "u-mikhail-02",
        "username": "Михаил Ковалев",
        "role": "Проводник 1-й кат.",
        "badge": "ВСМ-1 • Бизнес-класс",
        "shifts_count": 24,
        "service_psychology": 92,
        "safety_tech": 95,
        "routine_discipline": 90,
        "first_aid": 85,
        "loyalty_score": 92,
    },
    {
        "id": "u-senior-01",
        "username": "Алексей Смирнов",
        "role": "Старший проводник",
        "badge": "ВСМ-1 • Бизнес-класс",
        "shifts_count": 14,
        "service_psychology": 85,
        "safety_tech": 100,
        "routine_discipline": 65,
        "first_aid": 40,
        "loyalty_score": 85,
    },
    {
        "id": "u-anna-04",
        "username": "Анна Родионова",
        "role": "Проводник",
        "badge": "ВСМ-1 • Эконом+",
        "shifts_count": 9,
        "service_psychology": 80,
        "safety_tech": 85,
        "routine_discipline": 80,
        "first_aid": 75,
        "loyalty_score": 82,
    },
    {
        "id": "u-trainee-02",
        "username": "Дмитрий Волков",
        "role": "Проводник-стажер",
        "badge": "ВСМ-1 • Стажер",
        "shifts_count": 2,
        "service_psychology": 45,
        "safety_tech": 50,
        "routine_discipline": 40,
        "first_aid": 35,
        "loyalty_score": 62,
    },
]

async def init_db() -> None:
    """Асинхронная инициализация таблиц и сидинг данных."""
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Таблица пользователей (проводников)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                badge TEXT NOT NULL,
                shifts_count INTEGER DEFAULT 0,
                service_psychology INTEGER DEFAULT 85,
                safety_tech INTEGER DEFAULT 100,
                routine_discipline INTEGER DEFAULT 65,
                first_aid INTEGER DEFAULT 40,
                loyalty_score INTEGER DEFAULT 85
            )
        """)

        # Таблица журнала действий симуляции
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
        try:
            await conn.execute("ALTER TABLE action_logs ADD COLUMN safety_delta INTEGER DEFAULT 0")
        except Exception:
            pass

        # Таблица достижений проводников
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

        # Проверка наличия данных и начальный сидинг
        async with conn.execute("SELECT COUNT(*) as count FROM users") as cursor:
            row = await cursor.fetchone()
            if row and row["count"] == 0:
                for u in INITIAL_SEED_USERS:
                    await conn.execute("""
                        INSERT INTO users (
                            id, username, role, badge, shifts_count,
                            service_psychology, safety_tech, routine_discipline, first_aid, loyalty_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        u["id"], u["username"], u["role"], u["badge"], u["shifts_count"],
                        u["service_psychology"], u["safety_tech"], u["routine_discipline"], u["first_aid"], u["loyalty_score"]
                    ))
                await conn.commit()

async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Асинхронное получение пользователя по ID."""
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_leaderboard() -> List[Dict[str, Any]]:
    """Асинхронное получение лидерборда."""
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM users ORDER BY loyalty_score DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def log_action(
    user_id: str,
    incident_id: str,
    option_id: str,
    loyalty_delta: int,
    safety_delta: int = 0,
    feedback: str = ""
) -> Optional[Dict[str, Any]]:
    """Логирует действие и обновляет метрики пользователя."""
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        
        # Получаем пользователя
        async with conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            user_row = await cursor.fetchone()
            if not user_row:
                return None

        now_str = datetime.utcnow().isoformat()
        
        # Записываем в лог
        await conn.execute("""
            INSERT INTO action_logs (user_id, timestamp, incident_id, option_id, loyalty_delta, safety_delta, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, now_str, incident_id, option_id, loyalty_delta, safety_delta, feedback))

        # Пересчитываем очки
        user = dict(user_row)
        new_loyalty = max(0, min(100, user["loyalty_score"] + loyalty_delta))
        new_safety = max(0, min(100, user["safety_tech"] + safety_delta))
        
        new_service = user["service_psychology"]
        new_discipline = user["routine_discipline"]
        new_first_aid = user["first_aid"]

        if loyalty_delta > 0:
            new_service = min(100, new_service + 4)
            new_discipline = min(100, new_discipline + 3)
        else:
            new_service = max(20, new_service - 2)

        # Анализ ID инцидента для прокачки специфичных навыков
        if any(kw in incident_id for kw in ["air", "temp", "vent", "climate"]):
            new_safety = min(100, new_safety + 3)
        if any(kw in incident_id for kw in ["med", "help", "doctor", "pills", "kinetosis"]):
            new_first_aid = min(100, new_first_aid + 5)

        # Обновляем пользователя
        await conn.execute("""
            UPDATE users
            SET loyalty_score = ?,
                safety_tech = ?,
                service_psychology = ?,
                routine_discipline = ?,
                first_aid = ?
            WHERE id = ?
        """, (new_loyalty, new_safety, new_service, new_discipline, new_first_aid, user_id))

        await conn.commit()

        # Автоматическая выдача достижений по регламентным ситуациям СТО РЖД
        if incident_id == "inc_vape_smoke_01" and option_id in ("opt_1", "opt_2_correct"):
            await unlock_achievement(user_id, "safety_first")
        elif incident_id == "inc_kinetosis_01" and option_id in ("opt_1", "opt_2_correct"):
            await unlock_achievement(user_id, "med_hero")
        elif incident_id == "inc_med_pills_01" and option_id in ("opt_2", "opt_2_correct"):
            await unlock_achievement(user_id, "sto_expert")

        # Возвращаем обновленного пользователя
        async with conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            updated_row = await cursor.fetchone()
            return dict(updated_row) if updated_row else None


ACHIEVEMENTS_CATALOG = {
    "first_trip": {
        "title": "Первый рейс ВСМ",
        "description": "Успешно доехать до Санкт-Петербурга по графику",
        "icon": "🚄"
    },
    "safety_first": {
        "title": "Страж безопасности",
        "description": "Пресечь курение вейпа и защитить пожарную систему",
        "icon": "🛡️"
    },
    "med_hero": {
        "title": "Скорая помощь 400 км/ч",
        "description": "Оказать правильную помощь при кинетозе без лишней паники",
        "icon": "🩺"
    },
    "sto_expert": {
        "title": "Знаток СТО РЖД",
        "description": "Отказать в выдаче личных лекарств строго по регламенту",
        "icon": "📜"
    }
}


async def unlock_achievement(user_id: str, code: str) -> Optional[Dict[str, Any]]:
    if code not in ACHIEVEMENTS_CATALOG:
        return None
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT id FROM user_achievements WHERE user_id = ? AND code = ?",
            (user_id, code)
        ) as c:
            if await c.fetchone():
                return None  # Уже открыта
        
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
            (user_id,)
        ) as c:
            rows = await c.fetchall()
            return [dict(r) for r in rows]

