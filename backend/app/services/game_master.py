import random
from typing import Dict, Any, List, Optional
from app.schemas.passenger import ActiveIncidentSchema, SeatInfo
from app.services.scenarios import SCENARIOS_DB, get_frontend_incident_data
from app.services.lessons import LESSONS_DB

class GameMaster:
    """Оркестратор событий и инцидентов (State Machine).
    Обрабатывает тики времени и динамические состояния пассажиров."""

    def __init__(self):
        self.current_mode = "pro"
        self.active_triggers: List[Dict[str, Any]] = []
        self.crying_start_time: Optional[float] = None
        self.crying_seat_id: Optional[str] = None
        self.neighbor_complained: bool = False
        self.init_triggers()

    def init_triggers(self, mode: str = "pro", start_time: float = 50400.0) -> None:
        self.current_mode = mode
        self.crying_start_time = None
        self.crying_seat_id = None
        self.neighbor_complained = False

        if mode.startswith("lesson_"):
            self.active_triggers = []
            return

        # Триггеры для режима PRO:
        # 1. 14:01:40 (start + 100) -> Пассивный пьяный пассажир (phase="passive")
        # 2. 14:06:00 (start + 360) -> Плачущий ребёнок (phase="ambient")
        # 3. 14:18:00 (start + 1080) -> Пролитый горячий чай (phase="urgent")
        # 4. 14:32:00 (start + 1920) -> Вейпер в салоне (phase="urgent")
        self.active_triggers = [
            {
                "id": "trig_drunk",
                "incident_id": "live_drunk",
                "time_sec": start_time + 100,
                "triggered": False,
                "phase": "passive",
            },
            {
                "id": "trig_crying",
                "incident_id": "live_crying_child",
                "time_sec": start_time + 360,
                "triggered": False,
                "phase": "ambient",
            },
            {
                "id": "trig_tea",
                "incident_id": "live_spilled_tea",
                "time_sec": start_time + 1080,
                "triggered": False,
                "phase": "urgent",
            },
            {
                "id": "trig_vaper",
                "incident_id": "live_vaper",
                "time_sec": start_time + 1920,
                "triggered": False,
                "phase": "urgent",
            },
        ]

    def process_tick(self, current_time: float, seats: List[SeatInfo]) -> List[Dict[str, Any]]:
        """Обрабатывает тик времени (вызывается на каждые 5 сек синхронизации или локальном тике).
        Возвращает список новых событий, если они активировались."""
        fired_events = []
        occupied = [s for s in seats if s.is_occupied and s.passenger]
        if not occupied:
            return fired_events

        # 1. Проверяем запланированные триггеры
        for trig in self.active_triggers:
            if not trig["triggered"] and current_time >= trig["time_sec"]:
                trig["triggered"] = True
                inc_id = trig["incident_id"]

                # Выбираем подходящее кресло
                candidates = [s for s in occupied if not s.active_incident]
                if not candidates:
                    candidates = occupied

                if inc_id == "live_crying_child":
                    target_seat = next((s for s in candidates if s.passenger.archetype_id == "female_young"), random.choice(candidates))
                elif inc_id == "live_drunk":
                    target_seat = next((s for s in candidates if s.passenger.archetype_id == "male_young"), random.choice(candidates))
                else:
                    target_seat = random.choice(candidates)

                inc_data = get_frontend_incident_data(inc_id)
                if inc_data:
                    inc_data["phase"] = trig.get("phase", inc_data.get("phase", "urgent"))
                    target_seat.active_incident = ActiveIncidentSchema(**inc_data)

                    # Меняем состояние и спрайт пассажира
                    if inc_id == "live_drunk":
                        target_seat.passenger.state = "drunk"
                        target_seat.passenger.sprite_url = f"/assets/passengers/{target_seat.passenger.archetype_id}/drunk.png"
                    elif inc_id == "live_crying_child":
                        self.crying_start_time = current_time
                        self.crying_seat_id = target_seat.seat_id
                        target_seat.passenger.state = "annoyed"
                        target_seat.passenger.sprite_url = f"/assets/passengers/{target_seat.passenger.archetype_id}/annoyed.png"
                    else:
                        target_seat.passenger.state = "annoyed"
                        target_seat.passenger.sprite_url = f"/assets/passengers/{target_seat.passenger.archetype_id}/annoyed.png"

                    fired_events.append({
                        "type": "incident_spawned",
                        "incident_id": inc_id,
                        "seat_id": target_seat.seat_id,
                        "phase": inc_data["phase"],
                    })

        # 2. Проверяем таймаут детского плача: жалоба соседа через 60 секунд!
        if self.crying_start_time and not self.neighbor_complained:
            crying_seat = next((s for s in seats if s.seat_id == self.crying_seat_id), None)
            has_crying = False
            if crying_seat and crying_seat.active_incident:
                c_inc = getattr(crying_seat.active_incident, "incident_id", None)
                if c_inc == "live_crying_child":
                    has_crying = True

            if has_crying:
                if current_time - self.crying_start_time >= 60:
                    neighbor_candidates = [
                        s for s in occupied 
                        if s.seat_id != self.crying_seat_id and not s.active_incident and abs(s.row - crying_seat.row) <= 1
                    ]
                    if not neighbor_candidates:
                        neighbor_candidates = [s for s in occupied if s.seat_id != self.crying_seat_id and not s.active_incident]

                    if neighbor_candidates:
                        neighbor_seat = random.choice(neighbor_candidates)
                        inc_data = get_frontend_incident_data("live_neighbor_complaint")
                        if inc_data:
                            neighbor_seat.active_incident = ActiveIncidentSchema(**inc_data)
                            neighbor_seat.passenger.state = "annoyed"
                            neighbor_seat.passenger.sprite_url = f"/assets/passengers/{neighbor_seat.passenger.archetype_id}/annoyed.png"
                            self.neighbor_complained = True
                            fired_events.append({
                                "type": "incident_spawned",
                                "incident_id": "live_neighbor_complaint",
                                "seat_id": neighbor_seat.seat_id,
                                "phase": "urgent",
                            })
            else:
                self.crying_start_time = None

        return fired_events

    def generate_timeline(self, mode: str = "pro", user: Optional[Dict[str, Any]] = None) -> dict:
        self.current_mode = mode
        user = user or {}
        timeline = []

        # РЕЖИМ: ОБУЧЕНИЕ (УРОК). Начинаем с Твери (14:38 -> 52680 сек)
        if mode.startswith("lesson_"):
            base_lesson_id = mode.rsplit("_", 1)[0] if "_" in mode and mode.rsplit("_", 1)[-1].isdigit() else mode
            lesson = LESSONS_DB.get(base_lesson_id)

            if lesson:
                start_time_sec = 52680  # 14:38 (Прибытие в Тверь)
                start_phase = "station_warning"

                incidents_list = lesson.get("incidents", [])
                sub_lesson_idx = int(mode.rsplit("_", 1)[1]) - 1 if "_" in mode and mode.rsplit("_", 1)[-1].isdigit() else None
                
                if sub_lesson_idx is not None and 0 <= sub_lesson_idx < len(incidents_list):
                    target_inc = incidents_list[sub_lesson_idx]["incident_id"]
                    timeline.append({
                        "id": "lesson_inc_0",
                        "type": "incident",
                        "timeSec": start_time_sec + 30,
                        "timeStr": "14:38:30",
                        "payload": target_inc
                    })
                else:
                    for idx, item in enumerate(incidents_list):
                        timeline.append({
                            "id": f"lesson_inc_{idx}",
                            "type": "incident",
                            "timeSec": start_time_sec + 30 + (idx * 600),
                            "timeStr": f"14:{38 + (idx * 10)}:30",
                            "payload": item["incident_id"]
                        })
                
                return {"timeline": timeline, "start_time": start_time_sec, "start_phase": start_phase}

        # РЕЖИМ: PRO. Начинаем с Москвы (14:00 -> 50400 сек)
        start_time_sec = 50400
        start_phase = "initial_round"
        
        # Адаптивный выбор инцидентов на основе слабых мест проводника
        skills = {
            "medicine": user.get("first_aid", 40),
            "safety": user.get("safety_tech", 100),
            "service": user.get("service_psychology", 85),
            "discipline": user.get("routine_discipline", 65)
        }
        weakest = min(skills.keys(), key=lambda k: skills[k])

        pool = []
        for inc_id in SCENARIOS_DB.keys():
            if weakest == "medicine" and ("med" in inc_id or "kinetosis" in inc_id):
                pool.append(inc_id)
            elif weakest == "safety" and ("vape" in inc_id or "bag" in inc_id or "luggage" in inc_id):
                pool.append(inc_id)
            elif weakest == "service" and ("noise" in inc_id or "broken" in inc_id or "seat" in inc_id):
                pool.append(inc_id)

        random.shuffle(pool)
        if len(pool) < 4:
            remaining = [k for k in SCENARIOS_DB.keys() if k not in pool]
            random.shuffle(remaining)
            pool.extend(remaining)

        selected_incidents = pool[:4]

        checkpoints_sec = [50880, 52200, 54240, 55920]
        for idx, inc_id in enumerate(selected_incidents):
            timeline.append({
                "id": f"pro_inc_{idx}",
                "type": "incident",
                "timeSec": checkpoints_sec[idx] if idx < len(checkpoints_sec) else 51000 + idx * 1200,
                "timeStr": f"14:{10 + idx * 15}:00",
                "payload": inc_id,
            })

        return {"timeline": timeline, "start_time": start_time_sec, "start_phase": start_phase}

    def spawn_incident(self, seats: List[SeatInfo], force_incident: Optional[str] = None) -> None:
        """Назначает инцидент случайному пассажиру."""
        for seat in seats:
            seat.active_incident = None

        occupied = [s for s in seats if s.is_occupied and s.passenger]
        if not occupied:
            return

        target_seat = random.choice(occupied)
        incident_id = force_incident or random.choice(list(SCENARIOS_DB.keys()))
        incident_data = get_frontend_incident_data(incident_id)

        if incident_data:
            target_seat.active_incident = ActiveIncidentSchema(**incident_data)
            new_state = SCENARIOS_DB.get(incident_id, {}).get("passenger_state_during", "annoyed")
            target_seat.passenger.state = new_state
            target_seat.passenger.sprite_url = f"/assets/passengers/{target_seat.passenger.archetype_id}/{new_state}.png"

    def apply_lesson_protection(self, result: dict) -> dict:
        """В режиме 'Урок' защищает от снятия баллов и дает обучающий фидбек."""
        res_copy = dict(result)
        if self.current_mode.startswith("lesson_"):
            if res_copy.get("loyalty_delta", 0) < 0:
                res_copy["loyalty_delta"] = 0
            if res_copy.get("safety_delta", 0) < 0:
                res_copy["safety_delta"] = 0
            
            if res_copy.get("mood") in ["annoyed", "drunk"]:
                res_copy["feedback_title"] = "Режим обучения: Штраф отменен"
                res_copy["feedback"] = f"В реальности это решение привело бы к жалобе. Попробуйте еще раз! Анализ: {res_copy.get('feedback', '')}"
        
        return res_copy
