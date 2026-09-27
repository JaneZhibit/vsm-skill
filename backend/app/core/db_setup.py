import os
import aiosqlite
from pathlib import Path

from app.core.db_seeds import INITIAL_SEED_USERS

BACKEND_DIR = Path(__file__).resolve().parents[2]
DB_PATH = os.getenv("VSM_DB_PATH", str(BACKEND_DIR / "vsm.db"))

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

        # Сидинг всех демо-пользователей
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
