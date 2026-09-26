from typing import Optional, Any, Dict
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
    mode: str = "adaptive"  # "adaptive" или "level_1"


class SpawnSpecificRequest(BaseModel):
    incident_id: str


@router.post("/trip/new")
async def create_new_trip(
    payload: Optional[TripInitRequest] = None,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Инициализирует новую персональную поездку."""
    mode = payload.mode if payload else "level_1"
    engine = trip_manager.create_trip(user["id"])

    # Генерируем таймлайн на бэкенде в зависимости от мода и навыков юзера
    timeline = engine.generate_timeline(mode=mode, user_skills=user)

    return {
        "manifest": engine.get_manifest(),
        "timeline": timeline,
    }


@router.post("/trip/spawn-specific", response_model=CabinManifestResponse)
async def trigger_specific_incident(
    payload: SpawnSpecificRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Вызывается фронтендом, когда таймлайн доходит до конкретного инцидента."""
    engine = trip_manager.get_trip(user["id"])
    engine.spawn_random_incident(force_incident=payload.incident_id)
    return engine.get_manifest()


@router.post("/trip/spawn-random", response_model=CabinManifestResponse)
async def trigger_random_incident(user: Dict[str, Any] = Depends(get_current_user)):
    """Вызывается фронтендом, когда таймлайн доходит до слота рандомного инцидента."""
    engine = trip_manager.get_trip(user["id"])
    engine.spawn_random_incident()
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
    """Сохраняет состояние (вызывается фронтендом каждые 5 сек)."""
    engine = trip_manager.get_trip(user["id"])
    engine.time_seconds = payload.time_seconds
    engine.speed = payload.speed
    engine.shift_phase = payload.shift_phase
    return {"status": "synced"}

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
    """Безопасная обработка инцидента. Роутер только маршрутизирует, всё остальное делают сервисы."""
    
    # 1. Получаем результаты сценария с бэкенда (никто не сможет считерить с фронта)
    scenario_result = get_scenario_result(payload.incident_id, payload.option_id)
    if not scenario_result:
        raise HTTPException(status_code=400, detail="Неверный ID инцидента или опции")

    # 2. Логируем в БД и обновляем скиллы пользователя
    safety_delta = scenario_result.get("safety_delta", 0)
    updated_user = await log_action(
        user_id=user["id"],
        incident_id=payload.incident_id,
        option_id=payload.option_id,
        loyalty_delta=scenario_result["loyalty_delta"],
        safety_delta=safety_delta,
        feedback=scenario_result["feedback"],
    )
    
    # 3. Делегируем обновление вагона движку (Инкапсуляция!)
    engine = trip_manager.get_trip(user["id"])
    engine.resolve_incident(
        incident_id=payload.incident_id,
        new_mood=scenario_result["mood"],
        loyalty_delta=scenario_result.get("loyalty_delta", 0)
    )

    return {
        "status": "resolved",
        "user": updated_user,
        "incident_result": scenario_result,
        "manifest": engine.get_manifest() # Отдаем обновленный вагон
    }


class CustomScenarioPayload(BaseModel):
    incident_id: str
    title: str
    prompt: str
    timer_seconds: int = 15
    opt_1_text: str
    opt_1_feedback: str
    opt_1_loyalty: int = 15
    opt_1_safety: int = 20
    opt_2_text: str
    opt_2_feedback: str
    opt_2_loyalty: int = -20
    opt_2_safety: int = -15


@router.post("/custom-scenario")
async def create_custom_scenario(payload: CustomScenarioPayload):
    """Позволяет добавить сценарий прямо из UI Студии без изменения кода ядра!"""
    SCENARIOS_DB[payload.incident_id] = {
        "title": payload.title,
        "passenger_state_during": "annoyed",
        "start_step": "step_1",
        "steps": {
            "step_1": {
                "prompt": payload.prompt,
                "timer_seconds": payload.timer_seconds,
                "options": [
                    {
                        "id": "opt_1",
                        "text": payload.opt_1_text,
                        "action_type": "click",
                        "result": {
                            "loyalty_delta": payload.opt_1_loyalty,
                            "safety_delta": payload.opt_1_safety,
                            "mood": "calm",
                            "feedback": payload.opt_1_feedback
                        }
                    },
                    {
                        "id": "opt_2",
                        "text": payload.opt_2_text,
                        "action_type": "click",
                        "result": {
                            "loyalty_delta": payload.opt_2_loyalty,
                            "safety_delta": payload.opt_2_safety,
                            "mood": "annoyed",
                            "feedback": payload.opt_2_feedback
                        }
                    }
                ]
            }
        }
    }
    return {"status": "created", "incident_id": payload.incident_id}


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
    """
    Принимает аудиозапись с микрофона проводника (в формате base64),
    транскрибирует через Whisper (Polza.ai) и оценивает через Gemini 2.5 Flash.
    """
    print(f"\n========================================================")
    print(f"🎙️ [VOICE-EXAM] Получен запрос по инциденту: {payload.incident_id}")
    print(f"========================================================")

    # 1. Получаем текст: либо транскрибируем аудио через Whisper, либо берем переданный текст
    conductor_speech = ""
    if payload.audio_base64:
        conductor_speech = await polza_ai.transcribe_audio_base64(payload.audio_base64, "audio/webm")
    elif payload.conductor_text:
        conductor_speech = payload.conductor_text.strip()

    if not conductor_speech:
        print("[VOICE-EXAM] Ошибка: речь не была распознана")
        return {
            "status": "empty_speech",
            "transcription": "",
            "incident_result": {
                "loyalty_delta": 0,
                "safety_delta": 0,
                "mood": "annoyed",
                "feedback_title": "Голос не распознан",
                "feedback": "Не удалось разобрать слова. Пожалуйста, повторите ответ четче в микрофон.",
                "is_passed": False,
                "role_model_steps": [],
                "transcription": ""
            }
        }

    # 2. Оцениваем через Gemini Flash (Polza.ai)
    incident_meta = SCENARIOS_DB.get(payload.incident_id, {})
    incident_title = incident_meta.get("title", payload.incident_id)

    eval_result = await polza_ai.evaluate_conductor_voice_response(
        incident_title=incident_title,
        passenger_prompt=payload.passenger_prompt or "",
        conductor_text=conductor_speech,
        expected_rule=payload.expected_rule or "СТО РЖД 03.011: Соблюдение комфорта и безопасности в скоростном движении",
    )

    loyalty_delta = int(eval_result.get("loyalty_delta", 15))
    safety_delta = int(eval_result.get("safety_delta", 20))
    feedback = eval_result.get("feedback_text", "Ответ оценен.")
    is_passed = eval_result.get("is_passed", True)
    mood = "calm" if is_passed else "annoyed"

    # 3. Фиксируем в базе данных прогресс проводника
    updated_user = await log_action(
        user_id=user["id"],
        incident_id=payload.incident_id,
        option_id="voice_response",
        loyalty_delta=loyalty_delta,
        safety_delta=safety_delta,
        feedback=feedback,
    )

    # 4. Обновляем статус вагона
    engine = trip_manager.get_trip(user["id"])
    engine.resolve_incident(
        incident_id=payload.incident_id,
        new_mood=mood,
        loyalty_delta=loyalty_delta,
    )

    return {
        "status": "resolved",
        "transcription": conductor_speech,
        "evaluation": eval_result,
        "user": updated_user,
        "manifest": engine.get_manifest(),
        "incident_result": {
            "loyalty_delta": loyalty_delta,
            "safety_delta": safety_delta,
            "mood": mood,
            "feedback": feedback,
            "feedback_title": eval_result.get("feedback_title", "Анализ ответа проводника"),
            "role_model_steps": eval_result.get("role_model_steps_covered", []),
            "is_passed": is_passed,
            "transcription": conductor_speech,
        },
    }


