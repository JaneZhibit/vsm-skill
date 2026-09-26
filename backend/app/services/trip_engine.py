"""
Движок поездки ВСМ-1 «Белый кречет» с математической моделью пассажиропотока.
Регламентирует сменяемость пассажиров на 16 станциях, соблюдает лимит 25 человек
и закон распределения дальности поездки.
"""

import random
import uuid
from typing import Literal, Optional

from app.schemas.passenger import (
    CabinManifestResponse,
    PassengerProfile,
    SeatInfo,
    StationEventResponse,
    ActiveIncidentSchema,
)
from app.services.passenger_generator import generate_passenger
from app.services.scenarios import SCENARIOS_DB, get_frontend_incident_data
from app.services.lessons import LESSONS_DB
from app.services.route_stations import (
    ROUTE_STATIONS,
    TOTAL_STATIONS,
    StationInfo,
)

MAX_PASSENGERS = 25
ALL_LETTERS: list[Literal["A", "B", "C", "D"]] = ["A", "B", "C", "D"]
ALL_SEAT_IDS = [f"{r}{l}" for r in range(1, 13) for l in ALL_LETTERS]


def get_destination_weight(k: int) -> float:
    """
    Возвращает вес вероятности дальности поездки (в количестве станций вперед k):
    k = 1: 1 (1%)
    k = 2: 5 (5%)
    k = 3: 10 (10%)
    k = 4: 20 (20%)
    k = 5: 35 (35%)
    k >= 6: 50 (~50%)
    """
    if k <= 1:
        return 1.0
    elif k == 2:
        return 5.0
    elif k == 3:
        return 10.0
    elif k == 4:
        return 20.0
    elif k == 5:
        return 35.0
    else:
        return 50.0


def select_destination(from_station_index: int) -> str:
    """
    Разыгрывает целевую станцию высадки для пассажира, садящегося на станции from_station_index.
    Исключает технические станции (Горки, Тигода).
    """
    # Кандидаты: все последующие станции маршрута
    candidates: list[StationInfo] = []
    weights: list[float] = []

    for idx in range(from_station_index + 1, TOTAL_STATIONS):
        st = ROUTE_STATIONS[idx]
        if st.is_technical:
            continue  # Пропускаем технические станции

        k = idx - from_station_index
        w = get_destination_weight(k)

        # Особое условие для Обухово-2 как пункта назначения:
        # Пассажиры из Москвы/Твери редко едут именно в Обухово вместо Московского вокзала СПб
        if st.name == "Обухово-2":
            w *= 0.1

        candidates.append(st)
        weights.append(w)

    if not candidates:
        return ROUTE_STATIONS[-1].name

    chosen = random.choices(candidates, weights=weights, k=1)[0]
    return chosen.name


class TripEngine:
    """Служба управления жизненным циклом поездки и пассажиропотоком вагона «Комфорт»."""

    def __init__(self):
        self.trip_id: str = str(uuid.uuid4())
        self.current_station_index: int = 0

        # Добавляем физическое состояние поезда
        self.time_seconds: float = 50400.0  # 14:00 в секундах
        self.speed: float = 0.0
        self.shift_phase: str = "initial_round"

        self.seats: list[SeatInfo] = []
        self.create_new_trip()

    def generate_timeline(self, mode: str = "level_1", user_skills: Optional[dict] = None) -> list:
        user_skills = user_skills or {}
        timeline = []

        # ---------------------------------------------------------
        # РЕЖИМ 1: ТЕМАТИЧЕСКИЙ УРОК ИЗ JSON (напр. "lesson_service" или "lesson_service_1")
        # ---------------------------------------------------------
        lesson_key = mode
        sub_lesson_idx = None
        if lesson_key not in LESSONS_DB and "_" in mode:
            parts = mode.rsplit("_", 1)
            if parts[0] in LESSONS_DB and parts[1].isdigit():
                lesson_key = parts[0]
                sub_lesson_idx = int(parts[1]) - 1

        if lesson_key in LESSONS_DB:
            lesson = LESSONS_DB[lesson_key]
            start_time = 50400  # 14:00:00 (старт урока)
            incidents_list = lesson.get("incidents", [])

            # Если выбран конкретный подурок (напр. lesson_service_1)
            if sub_lesson_idx is not None and 0 <= sub_lesson_idx < len(incidents_list):
                target_item = incidents_list[sub_lesson_idx]
                timeline.append({
                    "id": f"lesson_{sub_lesson_idx}_{target_item['incident_id']}",
                    "type": "incident",
                    "timeSec": start_time + 15,
                    "timeStr": "14:00:15",
                    "payload": target_item["incident_id"],
                })
            else:
                for idx, item in enumerate(incidents_list):
                    inc_id = item["incident_id"]
                    delay = item.get("delay_seconds", 30)
                    event_time = start_time + delay

                    timeline.append({
                        "id": f"lesson_{idx}_{inc_id}",
                        "type": "incident",
                        "timeSec": event_time,
                        "timeStr": f"14:0{idx}:00",
                        "payload": inc_id,
                    })

            timeline.sort(key=lambda x: x["timeSec"])
            return timeline

        # ---------------------------------------------------------
        # РЕЖИМ 2: ПОЛНОЦЕННЫЙ РЕЙС (level_1 или adaptive экзамен)
        # ---------------------------------------------------------
        # 1. Прибытия на 15 станций по эталонному графику
        for st in ROUTE_STATIONS[1:]:
            timeline.append({
                "id": f"st_{st.index}",
                "type": "station_arrival",
                "timeSec": st.planned_seconds,
                "timeStr": st.planned_time,
                "payload": st.index,
            })

        # 2. Выбираем инциденты из нашего пула 10 сценариев
        all_incidents = list(SCENARIOS_DB.keys())
        if all_incidents:
            # Распределяем 4 ключевых инцидента на крейсерских перегонах
            checkpoints_sec = [50880, 52200, 54240, 55920]
            selected = all_incidents[:4] if len(all_incidents) >= 4 else all_incidents

            for idx, inc_id in enumerate(selected):
                timeline.append({
                    "id": f"trip_inc_{idx}",
                    "type": "incident",
                    "timeSec": checkpoints_sec[idx] if idx < len(checkpoints_sec) else 51000 + idx * 1200,
                    "timeStr": f"14:{10 + idx * 15}:00",
                    "payload": inc_id,
                })

        timeline.sort(key=lambda x: x["timeSec"])
        return timeline

    def spawn_random_incident(self, force_incident: Optional[str] = None):
        """Случайно выбирает занятое место и назначает ему инцидент."""
        for seat in self.seats:
            seat.active_incident = None

        occupied_seats = [s for s in self.seats if s.is_occupied and s.passenger]
        if not occupied_seats:
            return

        target_seat = random.choice(occupied_seats)
        incident_id = force_incident or random.choice(list(SCENARIOS_DB.keys()))

        incident_data = get_frontend_incident_data(incident_id)
        if incident_data:
            # 1. Обязательно оборачиваем словарь в Pydantic-модель!
            target_seat.active_incident = ActiveIncidentSchema(**incident_data)
            
            # 2. Меняем статус и ОБНОВЛЯЕМ ПУТЬ К КАРТИНКЕ
            new_state = SCENARIOS_DB[incident_id].get("passenger_state_during", "annoyed")
            target_seat.passenger.state = new_state
            target_seat.passenger.sprite_url = f"/assets/passengers/{target_seat.passenger.archetype_id}/{new_state}.png"

    def create_new_trip(
        self,
        min_passengers: int = 13,
        max_passengers: int = 18,
    ) -> CabinManifestResponse:
        self.trip_id = str(uuid.uuid4())
        self.current_station_index = 0
        self.time_seconds = 50400.0  # 14:00 (если ты добавлял физику из предыдущего шага)
        self.speed = 0.0
        self.shift_phase = "initial_round"

        target_count = random.randint(min_passengers, max_passengers)
        target_count = min(target_count, MAX_PASSENGERS)

        # Случайно выбираем места для посадки (без привязки к 2A)
        chosen_seats = random.sample(ALL_SEAT_IDS, target_count)
        occupied_seat_set = set(chosen_seats)

        seats_list: list[SeatInfo] = []

        for seat_id in ALL_SEAT_IDS:
            row = int(seat_id[:-1])
            letter = seat_id[-1]

            if seat_id in occupied_seat_set:
                dest = select_destination(0)
                # Генерируем обычного пассажира (но is_boarding=True, значит он не спит)
                t_status = "validated" if random.random() < 0.6 else "not_checked"
                prof = generate_passenger(destination=dest, ticket_status=t_status, is_boarding=True)
                seats_list.append(
                    SeatInfo(seat_id=seat_id, row=row, letter=letter, is_occupied=True, passenger=prof)
                )
            else:
                seats_list.append(
                    SeatInfo(seat_id=seat_id, row=row, letter=letter, is_occupied=False, passenger=None)
                )

        self.seats = seats_list

        return self.get_manifest()

    def get_manifest(self) -> CabinManifestResponse:
        """Возвращает текущий манифест вагона."""
        occupied = sum(1 for s in self.seats if s.is_occupied)
        validated = sum(
            1
            for s in self.seats
            if s.is_occupied and s.passenger and s.passenger.ticket_status == "validated"
        )
        return CabinManifestResponse(
            train_number="754",
            wagon_number="03",
            wagon_class="Комфорт",
            total_seats=48,
            occupied_count=occupied,
            validated_count=validated,
            seats=self.seats,
        )

    def process_station_arrival(self, station_index: int) -> StationEventResponse:
        """
        Обрабатывает прибытие поезда на станцию station_index:
        1. Высаживает пассажиров, у которых destination совпадает со станцией.
        2. Если станция пассажирская и не конечная — сажает новых до лимита 25 чел.
        """
        if station_index < 0 or station_index >= TOTAL_STATIONS:
            station_index = min(max(0, station_index), TOTAL_STATIONS - 1)

        st = ROUTE_STATIONS[station_index]
        self.current_station_index = station_index

        disembarked_names: list[str] = []
        boarded_names: list[str] = []

        # 1. Если станция техническая — пропуск
        if st.is_technical:
            return StationEventResponse(
                station_index=station_index,
                station_name=st.name,
                is_technical=True,
                disembarked_count=0,
                disembarked_passengers=[],
                boarded_count=0,
                boarded_passengers=[],
                total_passengers=sum(1 for s in self.seats if s.is_occupied),
                manifest=self.get_manifest(),
            )

        # 2. Высадка прибывших пассажиров
        is_final_station = station_index == TOTAL_STATIONS - 1

        for seat in self.seats:
            if seat.is_occupied and seat.passenger:
                # Пассажир выходит, если его станция совпадает с текущей, или это конечная
                if seat.passenger.destination == st.name or is_final_station:
                    disembarked_names.append(seat.passenger.full_name)
                    seat.is_occupied = False
                    seat.passenger = None
                    seat.active_incident = None  # <--- Очищаем инцидент у вышедшего пассажира!

        # 3. Посадка новых пассажиров (только если станция не конечная)
        if not is_final_station:
            current_occupied = sum(1 for s in self.seats if s.is_occupied)
            available_slots = max(0, MAX_PASSENGERS - current_occupied)

            if st.name == "Обухово-2":
                # На предпоследней станции Обухово-2 вероятность посадки 1%, не более 1 чел
                incoming_count = 1 if (available_slots > 0 and random.random() < 0.01) else 0
            else:
                raw_incoming = round(random.uniform(1.0, 3.0) * st.weight)
                incoming_count = min(available_slots, max(0, raw_incoming))

            # Свободные кресла
            free_seats = [s for s in self.seats if not s.is_occupied]
            random.shuffle(free_seats)

            for i in range(min(incoming_count, len(free_seats))):
                seat = free_seats[i]
                dest = select_destination(station_index)
                new_prof = generate_passenger(
                    destination=dest,
                    ticket_status="not_checked",  # Новые пассажиры ждут проверки АСКП
                )
                seat.is_occupied = True
                seat.passenger = new_prof
                boarded_names.append(new_prof.full_name)

        return StationEventResponse(
            station_index=station_index,
            station_name=st.name,
            is_technical=False,
            disembarked_count=len(disembarked_names),
            disembarked_passengers=disembarked_names,
            boarded_count=len(boarded_names),
            boarded_passengers=boarded_names,
            total_passengers=sum(1 for s in self.seats if s.is_occupied),
            manifest=self.get_manifest(),
        )

    def resolve_incident(self, incident_id: str, new_mood: str, loyalty_delta: int) -> None:
        """Внутренняя логика обновления пассажира после решения инцидента."""
        for seat in self.seats:
            if not seat.active_incident:
                continue

            # Безопасное извлечение ID (может быть dict или объект Pydantic)
            inc_id = seat.active_incident.get("incident_id") if isinstance(seat.active_incident, dict) else getattr(seat.active_incident, "incident_id", None)

            if inc_id == incident_id:
                seat.active_incident = None
                if seat.passenger:
                    seat.passenger.state = new_mood
                    # Обновляем путь к картинке в зависимости от нового настроения
                    sprite_mood = "neutral" if new_mood == "calm" else new_mood
                    seat.passenger.sprite_url = f"/assets/passengers/{seat.passenger.archetype_id}/{sprite_mood}.png"

                    # Если решение позитивное — билет считаем проверенным (лояльность выросла)
                    if loyalty_delta > 0 or new_mood in ["calm", "happy", "neutral"]:
                        seat.passenger.ticket_status = "validated"
                break


class TripManager:
    """Управляет независимыми сессиями поездок для разных пользователей."""

    def __init__(self):
        # Ключ - user_id, Значение - экземпляр TripEngine
        self.active_trips: dict[str, TripEngine] = {}

    def get_trip(self, user_id: str) -> TripEngine:
        """Возвращает текущую поездку пользователя или создает новую."""
        if user_id not in self.active_trips:
            self.active_trips[user_id] = TripEngine()
        return self.active_trips[user_id]

    def create_trip(self, user_id: str) -> TripEngine:
        """Принудительно пересоздает поездку (для кнопки 'Новая поездка')."""
        self.active_trips[user_id] = TripEngine()
        return self.active_trips[user_id]


# Глобальный менеджер поездок для бэкенда
trip_manager = TripManager()
