import uuid
from typing import Optional, Dict, Any
from app.schemas.passenger import CabinManifestResponse, StationEventResponse
from app.services.passenger_manager import PassengerManager
from app.services.game_master import GameMaster
from app.services.trip_engine_utils import MAX_PASSENGERS

class TripEngine:
    """Оркестратор поездки. Связывает физику, пассажиров и ИИ-дирижера."""

    def __init__(self):
        self.trip_id: str = str(uuid.uuid4())
        self.time_seconds: float = 50400.0
        self.speed: float = 0.0
        self.shift_phase: str = "initial_round"
        
        self.passenger_manager = PassengerManager()
        self.game_master = GameMaster()
        self.passenger_manager.generate_empty_manifest()

    def create_new_trip(
        self,
        mode: str = "pro",
        user: Optional[Dict[str, Any]] = None,
        min_passengers: int = 13,
        max_passengers: int = 18,
    ) -> dict:
        """Создает новый рейс, возвращая таймлайн и стартовую позицию."""
        user = user or {}
        self.trip_id = str(uuid.uuid4())
        
        # 1. Генерируем таймлайн и стартовые условия через Game Master
        setup = self.game_master.generate_timeline(mode, user)
        self.time_seconds = setup["start_time"]
        self.shift_phase = setup["start_phase"]
        self.speed = 0.0  # Поезд стоит на станции
        self.game_master.init_triggers(mode=mode, start_time=self.time_seconds)
        
        # 2. Вагон ПУСТ при старте смены в 13:50 (Приемка), либо заселен если это Урок
        if mode.startswith("lesson_"):
            self.passenger_manager.generate_initial_manifest(
                min_passengers=min_passengers,
                max_passengers=max_passengers,
            )
        else:
            self.passenger_manager.generate_empty_manifest()

        return {
            "manifest": self.passenger_manager.get_manifest(),
            "timeline": setup["timeline"],
            "start_time_seconds": self.time_seconds,
            "start_phase": self.shift_phase
        }

    def board_passengers(self, min_passengers: int = 13, max_passengers: int = 18) -> CabinManifestResponse:
        """Осуществляет посадку пассажиров перед самым отправлением."""
        self.passenger_manager.generate_initial_manifest(
            min_passengers=min_passengers,
            max_passengers=max_passengers,
        )
        self.shift_phase = "cruise"
        self.time_seconds = 50400.0  # Устанавливаем ровно на 14:00 (Отправление)
        return self.passenger_manager.get_manifest()

    def generate_timeline(self, mode: str = "pro", user: Optional[Dict[str, Any]] = None) -> list:
        setup = self.game_master.generate_timeline(mode, user)
        return setup.get("timeline", [])

    def get_manifest(self) -> CabinManifestResponse:
        return self.passenger_manager.get_manifest()

    def spawn_incident(self, force_incident: Optional[str] = None):
        self.game_master.spawn_incident(self.passenger_manager.seats, force_incident)
        return self.get_manifest()

    def process_tick(self, current_time: float, current_speed: Optional[float] = None) -> list:
        self.time_seconds = current_time
        speed = current_speed if current_speed is not None else getattr(self, "speed", 250.0)
        return self.game_master.process_tick(current_time, speed, self.passenger_manager.seats)

    def process_station_arrival(self, station_index: int) -> StationEventResponse:
        return self.passenger_manager.process_station(station_index)

    def resolve_incident(self, incident_id: str, raw_result: Optional[dict] = None, **kwargs) -> None:
        """Обновляет статус вагона после решения ИИ или клика по кнопке."""
        if raw_result is None:
            raw_result = {
                "mood": kwargs.get("new_mood", "calm"),
                "loyalty_delta": kwargs.get("loyalty_delta", 0),
            }

        # GameMaster может отменить штрафы в режиме урока
        final_result = self.game_master.apply_lesson_protection(raw_result)
        new_mood = final_result.get("mood", "calm")
        loyalty_delta = final_result.get("loyalty_delta", 0)

        for seat in self.passenger_manager.seats:
            inc_id = None
            if seat.active_incident:
                inc_id = seat.active_incident.get("incident_id") if isinstance(seat.active_incident, dict) else getattr(seat.active_incident, "incident_id", None)

            if inc_id == incident_id or seat.seat_id == incident_id:
                if seat.active_incident:
                    seat.active_incident = None
                if seat.passenger:
                    seat.passenger.state = new_mood
                    sprite_mood = "neutral" if new_mood == "calm" else new_mood
                    seat.passenger.sprite_url = f"/assets/{seat.passenger.archetype_id}/{sprite_mood}.png"

                    if loyalty_delta > 0 or new_mood in ["calm", "happy", "neutral"]:
                        seat.passenger.ticket_status = "validated"
                break


class TripManager:
    def __init__(self):
        self.active_trips: dict[str, TripEngine] = {}

    def get_trip(self, user_id: str) -> TripEngine:
        if user_id not in self.active_trips:
            self.active_trips[user_id] = TripEngine()
        return self.active_trips[user_id]

    def create_trip(self, user_id: str) -> TripEngine:
        self.active_trips[user_id] = TripEngine()
        return self.active_trips[user_id]

trip_manager = TripManager()
