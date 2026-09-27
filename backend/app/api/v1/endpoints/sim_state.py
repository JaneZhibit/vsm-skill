from typing import Optional, Any, Dict, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.endpoints.users import get_current_user
from app.schemas.passenger import (
    CabinManifestResponse,
    StationEventRequest,
    StationEventResponse,
    TripStatePayload,
)
from app.services.trip_engine import trip_manager
from app.services.route_stations import ROUTE_STATIONS

router = APIRouter()

@router.get("/cabin-manifest", response_model=CabinManifestResponse)
async def get_cabin_manifest(user: Dict[str, Any] = Depends(get_current_user)):
    """Возвращает текущий манифест вагона для конкретного пользователя."""
    engine = trip_manager.get_trip(user["id"])
    return engine.get_manifest()

class TripInitRequest(BaseModel):
    mode: str = "pro"

@router.post("/trip/new")
async def create_new_trip(
    payload: Optional[TripInitRequest] = None,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Инициализирует новую персональную поездку."""
    mode = payload.mode if payload else "pro"
    engine = trip_manager.create_trip(user["id"])
    trip_data = engine.create_new_trip(mode=mode, user=user)
    return trip_data

@router.post("/trip/board", response_model=CabinManifestResponse)
async def board_passengers_to_train(user: Dict[str, Any] = Depends(get_current_user)):
    """Осуществляет посадку пассажиров. Переход от Приемки к Рейсу."""
    engine = trip_manager.get_trip(user["id"])
    return engine.board_passengers()

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
