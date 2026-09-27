from typing import Optional, Any, Dict, List, Literal
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel

from app.core.database import log_action
from app.api.v1.endpoints.users import get_current_user
from app.schemas.passenger import (
    CabinManifestResponse,
    StationEventRequest,
    StationEventResponse,
    TripStatePayload,
)
from app.services.trip_engine import trip_manager
from app.services.route_stations import ROUTE_STATIONS
from app.services.scenarios import get_scenario_result, SCENARIOS_DB
from app.services.polza_service import polza_ai

router = APIRouter()

@router.get("/cabin-manifest", response_model=CabinManifestResponse)
async def get_cabin_manifest(user: Dict[str, Any] = Depends(get_current_user)):
    """Возвращает текущий манифест вагона для конкретного пользователя."""
    engine = trip_manager.get_trip(user["id"])
    return engine.get_manifest()

class TripInitRequest(BaseModel):
    mode: str = "pro"


class SpawnSpecificRequest(BaseModel):
    incident_id: str


@router.post("/trip/new")
async def create_new_trip(
    payload: Optional[TripInitRequest] = None,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Инициализирует новую персональную поездку."""
    mode = payload.mode if payload else "pro"
    engine = trip_manager.create_trip(user["id"])

    # Создаем рейс, получаем манифест, таймлайн и стартовые координаты (Тверь или Москва)
    trip_data = engine.create_new_trip(mode=mode, user=user)

    return trip_data


@router.post("/trip/spawn-specific", response_model=CabinManifestResponse)
async def trigger_specific_incident(
    payload: SpawnSpecificRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    engine = trip_manager.get_trip(user["id"])
    engine.spawn_incident(force_incident=payload.incident_id)
    return engine.get_manifest()


@router.post("/trip/spawn-random", response_model=CabinManifestResponse)
async def trigger_random_incident(user: Dict[str, Any] = Depends(get_current_user)):
    engine = trip_manager.get_trip(user["id"])
    engine.spawn_incident()
    return engine.get_manifest()

@router.post("/trip/station-event", response_model=StationEventResponse)
async def process_station_event(payload: StationEventRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Обрабатывает прибытие на станцию для поездки пользователя."""
    engine = trip_manager.get_trip(user["id"])
    return engine.process_station_arrival(payload.station_index)

@router.get("/trip/state", response_model=TripStatePayload)
async def get_trip_state(user: Dict[str, Any] = Depends(get_current_user)):
    """Отдает текущее сохраненное время и скорость."""
    engine = trip_manager.get_trip(user["id"])
    return TripStatePayload(
        time_seconds=engine.time_seconds,
        speed=engine.speed,
        shift_phase=engine.shift_phase
    )

@router.post("/trip/state")
async def sync_trip_state(payload: TripStatePayload, user: Dict[str, Any] = Depends(get_current_user)):
    """Сохраняет состояние (вызывается фронтендом каждые 5 сек) и обрабатывает тики GameMaster."""
    engine = trip_manager.get_trip(user["id"])
    engine.speed = payload.speed
    engine.shift_phase = payload.shift_phase
    events = engine.process_tick(payload.time_seconds, payload.speed)
    return {
        "status": "synced",
        "events": events,
        "manifest": engine.get_manifest() if events else None,
    }

@router.get("/trip/stations")
async def get_route_stations():
    return [
        {
            "index": s.index, "name": s.name, "km": s.km,
            "planned_time": s.planned_time, "stop_duration_min": s.stop_duration_min,
            "is_technical": s.is_technical, "weight": s.weight, "description": s.description,
        } for s in ROUTE_STATIONS
    ]

# Новая схема запроса: фронтенд присылает только ID инцидента и ID решения
class ResolveIncidentRequest(BaseModel):
    incident_id: str
    option_id: str

@router.post("/resolve-incident")
async def resolve_simulation_incident(payload: ResolveIncidentRequest, user: Dict[str, Any] = Depends(get_current_user)):
    scenario_result = get_scenario_result(payload.incident_id, payload.option_id)
    if not scenario_result:
        raise HTTPException(status_code=400, detail="Неверный ID инцидента или опции")

    engine = trip_manager.get_trip(user["id"])
    
    # Сначала защищаем от штрафов, если это Урок
    protected_result = engine.game_master.apply_lesson_protection(scenario_result)

    # 🦋 ЭФФЕКТ БАБОЧКИ для кнопочного выбора (например opt_2 в inc_kinetosis_01) 🦋
    incident_meta = SCENARIOS_DB.get(payload.incident_id, {})
    step1 = incident_meta.get("steps", {}).get("step_1", {})
    chosen_opt = next((o for o in step1.get("options", []) if o.get("id") == payload.option_id), {})
    if chosen_opt.get("next_step") == "trigger_medic" or protected_result.get("butterfly_effect") == "inc_medic_search":
        engine.game_master.spawn_incident(engine.passenger_manager.seats, force_incident="inc_medic_search")

    # Логируем в БД уже защищенные баллы
    updated_user = await log_action(
        user_id=user["id"],
        incident_id=payload.incident_id,
        option_id=payload.option_id,
        loyalty_delta=protected_result["loyalty_delta"],
        safety_delta=protected_result.get("safety_delta", 0),
        feedback=protected_result.get("feedback", ""),
    )
    
    # Обновляем вагон
    engine.resolve_incident(payload.incident_id, protected_result)

    return {
        "status": "resolved",
        "user": updated_user,
        "incident_result": protected_result,
        "manifest": engine.get_manifest()
    }


class LiveScenarioTrigger(BaseModel):
    # orchestrator - решает ИИ, chained - цепная реакция, test - запуск по таймеру для тестов, time, speed, random
    type: Literal["orchestrator", "chained", "test", "time", "speed", "random"]
    value: Optional[int] = None          # Секунды (time) или км/ч (speed) или шанс % (random)
    parent_id: Optional[str] = None      # ID родительского инцидента (для chained)
    delay_sec: Optional[int] = 10        # Задержка в секундах (для test или chained)

class CustomLiveScenarioPayload(BaseModel):
    incident_id: Optional[str] = None
    title: str
    target_archetype: str  # "any", "male_young", "female_young", "female_elderly"
    trigger: LiveScenarioTrigger
    allowed_moods: List[str] = ["neutral", "angry", "happy"]  # ИИ выберет только из них
    ambient_audio: Optional[str] = None # "crying_child.mp3", "vape_hiss.mp3"
    passenger_state: Optional[str] = None
    is_passive: bool = False       # Если True - нет красного колокольчика, просто меняется стейт
    llm_system_prompt: str # Что ИИ должен отыгрывать (напр. "Ты куришь вейп...")
    expected_rule: str     # Что должен сказать проводник (для оценки LLM)
    skills: List[str] = [] # ["safety", "service", "discipline", "medicine"]

# Глобальный реестр пользовательских живых сценариев
LIVE_SCENARIOS_DB = {}

@router.get("/custom-live-scenario")
async def get_live_scenarios():
    """Отдает список всех созданных событий для связывания."""
    return [{"id": k, "title": v.get("title", k)} for k, v in LIVE_SCENARIOS_DB.items()]

@router.post("/custom-live-scenario")
async def create_live_scenario(payload: CustomLiveScenarioPayload):
    """No-Code редактор живых (эмерджентных) ситуаций."""
    import time
    inc_id = payload.incident_id or f"evt_{int(time.time()*1000)}"
    data = payload.model_dump()
    data["incident_id"] = inc_id
    passenger_state = payload.passenger_state or (payload.allowed_moods[0] if payload.allowed_moods else "neutral")
    data["passenger_state"] = passenger_state
    LIVE_SCENARIOS_DB[inc_id] = data
    SCENARIOS_DB[inc_id] = {
        "incident_id": inc_id,
        "title": payload.title,
        "phase": "passive" if payload.is_passive else "urgent",
        "passenger_state_during": passenger_state,
        "ai_persona": payload.llm_system_prompt,
        "start_step": "step_1",
        "skills": payload.skills,
        "allowed_moods": payload.allowed_moods,
        "ambient_audio": payload.ambient_audio,
        "steps": {
            "step_1": {
                "prompt": payload.llm_system_prompt,
                "expected_rule": payload.expected_rule,
                "phase": "passive" if payload.is_passive else "urgent",
                "options": []
            }
        }
    }
    return {"status": "created", "incident_id": inc_id}


class VoiceResolveRequest(BaseModel):
    incident_id: str
    audio_base64: Optional[str] = None
    conductor_text: Optional[str] = None
    passenger_prompt: Optional[str] = ""
    expected_rule: Optional[str] = ""

@router.post("/trip/voice-resolve")
async def resolve_voice_incident(
    payload: VoiceResolveRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    conductor_speech = ""
    if payload.audio_base64:
        conductor_speech = await polza_ai.transcribe_audio_base64(payload.audio_base64, "audio/webm")
    elif payload.conductor_text:
        conductor_speech = payload.conductor_text.strip()

    if not conductor_speech:
        return {
            "status": "empty_speech",
            "incident_result": {
                "loyalty_delta": 0,
                "safety_delta": 0,
                "mood": "annoyed",
                "passenger_reply": "Вы что-то сказали? Я не расслышал.",
                "feedback_title": "Голос не распознан",
                "feedback": "Повторите четче.",
                "is_passed": False
            }
        }

    engine = trip_manager.get_trip(user["id"])
    incident_meta = SCENARIOS_DB.get(payload.incident_id, {})
    ai_persona = incident_meta.get("ai_persona", "")
    allowed_moods = incident_meta.get("allowed_moods")

    # 1. Извлекаем полный профиль текущего пассажира
    active_seat = next((s for s in engine.passenger_manager.seats if s.active_incident), None)
    passenger_profile = active_seat.passenger.model_dump() if (active_seat and active_seat.passenger) else {}

    # 2. Быстрый вызов LLM (json_schema) с мега-промптом
    eval_result = await polza_ai.evaluate_conductor_voice_response(
        incident_title=incident_meta.get("title", payload.incident_id),
        passenger_prompt=payload.passenger_prompt,
        conductor_text=conductor_speech,
        expected_rule=payload.expected_rule or "СТО РЖД 03.011",
        passenger_profile=passenger_profile,
        conductor_gender=user.get("gender", "m"),
        ai_persona=ai_persona,
        allowed_moods=allowed_moods
    )
    eval_result = engine.game_master.apply_lesson_protection(eval_result)

    # 3. Синтезируем аудио ответа пассажира с динамическим голосом и темпом
    passenger_reply_text = eval_result.get("passenger_reply", "")
    passenger_audio_b64 = None
    if passenger_reply_text:
        archetype = passenger_profile.get("archetype_id", "female_young")
        trait = passenger_profile.get("trait", "polite")
        passenger_audio_b64 = await polza_ai.generate_speech_base64(passenger_reply_text, archetype, trait)

    # Эффект бабочки
    if "butterfly_effect" in eval_result:
        engine.game_master.spawn_incident(engine.passenger_manager.seats, force_incident=eval_result["butterfly_effect"])
        engine.resolve_incident(payload.incident_id, eval_result)
        return {
            "status": "resolved",
            "transcription": conductor_speech,
            "manifest": engine.get_manifest(),
            "incident_result": {
                "loyalty_delta": 0,
                "safety_delta": 0,
                "mood": "sick",
                "is_passed": True,
                "passenger_reply": passenger_reply_text,
                "passenger_audio_base64": passenger_audio_b64,
                "feedback": f"Пассажир ответил: «{passenger_reply_text}». Вы перешли к поиску помощи.",
                "feedback_title": "Эффект бабочки",
                "transcription": conductor_speech,
            },
        }

    # Обычное решение
    updated_user = await log_action(
        user_id=user["id"],
        incident_id=payload.incident_id,
        option_id="voice_response",
        loyalty_delta=eval_result.get("loyalty_delta", 0),
        safety_delta=eval_result.get("safety_delta", 0),
        feedback=eval_result.get("feedback_text", ""),
    )
    engine.resolve_incident(payload.incident_id, eval_result)

    return {
        "status": "resolved",
        "transcription": conductor_speech,
        "user": updated_user,
        "manifest": engine.get_manifest(),
        "incident_result": {
            "loyalty_delta": eval_result.get("loyalty_delta", 0),
            "safety_delta": eval_result.get("safety_delta", 0),
            "mood": eval_result.get("mood", "calm"),
            "passenger_reply": passenger_reply_text,
            "passenger_audio_base64": passenger_audio_b64,
            "feedback": eval_result.get("feedback_text", "Оценено."),
            "feedback_title": eval_result.get("feedback_title", "Анализ ответа"),
            "role_model_steps": eval_result.get("role_model_steps_covered", []),
            "is_passed": eval_result.get("is_passed", True),
            "transcription": conductor_speech,
        },
    }


