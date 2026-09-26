import json
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import PROJECT_ROOT, BACKEND_DIR

LESSONS_DIR = PROJECT_ROOT / "backend" / "data" / "lessons"
if not LESSONS_DIR.exists():
    LESSONS_DIR = BACKEND_DIR / "data" / "lessons"


def load_lessons() -> Dict[str, Dict[str, Any]]:
    """Сканирует папку lessons/ и загружает все уроки в единый реестр."""
    lessons_db: Dict[str, Dict[str, Any]] = {}
    if not LESSONS_DIR.exists():
        LESSONS_DIR.mkdir(parents=True, exist_ok=True)
        return lessons_db

    for file_path in LESSONS_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                lesson_id = data.get("lesson_id") or file_path.stem
                lessons_db[lesson_id] = data
        except Exception as e:
            print(f"Error loading lesson {file_path.name}: {e}")

    return lessons_db


LESSONS_DB = load_lessons()


def get_lesson(lesson_id: str) -> Optional[Dict[str, Any]]:
    return LESSONS_DB.get(lesson_id)
