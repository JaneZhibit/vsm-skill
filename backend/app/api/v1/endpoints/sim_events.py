from typing import Optional, List, Literal
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.services.scenarios import SCENARIOS_DB, SCENARIOS_DIR
import time
import json
import shutil
from app.core.config import PROJECT_ROOT, BACKEND_DIR

router = APIRouter()

class LiveScenarioTrigger(BaseModel):
    type: Literal["orchestrator", "chained", "test", "time", "speed", "random"]
    value: Optional[int] = None
    parent_id: Optional[str] = None
    delay_sec: Optional[int] = 10
    condition: Optional[str] = "ignored"

class CustomLiveScenarioPayload(BaseModel):
    incident_id: Optional[str] = None
    title: str
    target_archetype: str
    trigger: LiveScenarioTrigger
    allowed_moods: List[str] = ["neutral", "angry", "happy"]
    ambient_audio: Optional[str] = None
    passenger_state: Optional[str] = None
    is_passive: bool = False
    llm_system_prompt: str
    initial_phrase: Optional[str] = ""
    expected_rule: str
    skills: List[str] = []

LIVE_SCENARIOS_DB = {
    k: v for k, v in SCENARIOS_DB.items() if "trigger" in v or "ai_persona" in v or "llm_system_prompt" in v
}

@router.get("/custom-live-scenario")
async def get_live_scenarios():
    result = []
    for k, v in LIVE_SCENARIOS_DB.items():
        result.append({
            "id": k,
            "title": v.get("title", k),
            "target_archetype": v.get("target_archetype", "any"),
            "trigger": v.get("trigger", {}),
            "passenger_state": v.get("passenger_state", "neutral"),
            "ambient_audio": v.get("ambient_audio"),
            "is_passive": v.get("is_passive", False),
            "skills": v.get("skills", []),
            "expected_rule": v.get("expected_rule") or v.get("steps", {}).get("step_1", {}).get("expected_rule", ""),
            "initial_phrase": v.get("steps", {}).get("step_1", {}).get("prompt", ""),
            "llm_system_prompt": v.get("llm_system_prompt", ""),
        })
    return result

@router.post("/custom-live-scenario")
async def create_live_scenario(payload: CustomLiveScenarioPayload):
    inc_id = payload.incident_id or f"evt_{int(time.time()*1000)}"
    data = payload.model_dump()
    data["incident_id"] = inc_id
    passenger_state = payload.passenger_state or (payload.allowed_moods[0] if payload.allowed_moods else "neutral")
    data["passenger_state"] = passenger_state

    trigger_data = payload.trigger.model_dump() if hasattr(payload.trigger, "model_dump") else payload.trigger

    scenario_entry = {
        "incident_id": inc_id,
        "title": payload.title,
        "target_archetype": payload.target_archetype,
        "trigger": trigger_data,
        "allowed_moods": payload.allowed_moods,
        "ambient_audio": payload.ambient_audio,
        "is_passive": payload.is_passive,
        "skills": payload.skills,
        "llm_system_prompt": payload.llm_system_prompt,
        "expected_rule": payload.expected_rule,
        "phase": "passive" if payload.is_passive else "urgent",
        "passenger_state_during": passenger_state,
        "passenger_state": passenger_state,
        "ai_persona": payload.llm_system_prompt,
        "start_step": "step_1",
        "steps": {
            "step_1": {
                "prompt": payload.initial_phrase or payload.llm_system_prompt,
                "expected_rule": payload.expected_rule,
                "phase": "passive" if payload.is_passive else "urgent",
                "options": []
            }
        }
    }

    LIVE_SCENARIOS_DB[inc_id] = scenario_entry
    SCENARIOS_DB[inc_id] = scenario_entry

    try:
        SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = SCENARIOS_DIR / f"{inc_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(scenario_entry, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to persist scenario {inc_id}: {e}")

    return {"status": "created", "incident_id": inc_id}

@router.delete("/custom-live-scenario/{incident_id}")
async def delete_live_scenario(incident_id: str):
    LIVE_SCENARIOS_DB.pop(incident_id, None)
    SCENARIOS_DB.pop(incident_id, None)
    file_path = SCENARIOS_DIR / f"{incident_id}.json"
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            print(f"Failed to delete file {file_path}: {e}")
    return {"status": "deleted", "incident_id": incident_id}

@router.post("/upload-ambient-audio")
async def upload_ambient_audio(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(('.mp3', '.wav', '.ogg')):
        raise HTTPException(400, "Только аудиофайлы (mp3, wav, ogg)")
        
    storage_dir = PROJECT_ROOT / "storage"
    if not storage_dir.exists():
        storage_dir = BACKEND_DIR / "storage"
    ambient_dir = storage_dir / "audio" / "ambient"
    ambient_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = ambient_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"status": "uploaded", "filename": file.filename}


@router.get("/assets-list")
async def get_dynamic_assets():
    """
    Динамически сканирует папки и возвращает списки существующих
    эмбиент-звуков и картинок-эмоций персонажей.
    """
    # 1. Сканируем аудио
    storage_dir = PROJECT_ROOT / "storage"
    ambient_dir = storage_dir / "audio" / "ambient"

    audio_files = []
    if ambient_dir.exists():
        for f in ambient_dir.glob("*"):
            if f.suffix.lower() in ['.mp3', '.wav', '.ogg']:
                audio_files.append({"id": f.name, "label": f"🎵 {f.name}"})

    # 2. Сканируем картинки (спрайты)
    # В Vite статичные файлы лежат в папке public/assets
    frontend_assets_dir = PROJECT_ROOT / "frontend" / "public" / "assets"
    sprites_map = {}

    if frontend_assets_dir.exists():
        for arch_dir in frontend_assets_dir.iterdir():
            if arch_dir.is_dir() and arch_dir.name in ["male_young", "female_young", "female_elderly", "any"]:
                # Получаем имена файлов без расширения (например, "vaping_calm")
                moods = [f.stem for f in arch_dir.glob("*.png")]
                if moods:
                    sprites_map[arch_dir.name] = moods

    return {
        "audio": audio_files,
        "sprites": sprites_map
    }