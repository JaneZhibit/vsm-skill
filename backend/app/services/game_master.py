import random
from typing import Dict, Any, List, Optional
from app.schemas.passenger import ActiveIncidentSchema, SeatInfo
from app.services.scenarios import SCENARIOS_DB, get_frontend_incident_data
from app.services.lessons import LESSONS_DB

class GameMaster:
    """Оркестратор инцидентов. Подстраивается под режим и навыки игрока."""

    def __init__(self):
        self.current_mode = "pro"

    def generate_timeline(self, mode: str = "pro", user: Optional[Dict[str, Any]] = None) -> dict:
        self.current_mode = mode
        user = user or {}
        timeline = []

        # РЕЖИМ: ОБУЧЕНИЕ (УРОК). Начинаем с Твери (14:38 -> 52680 сек)
        if mode.startswith("lesson_"):
            # Вытягиваем базовый lesson_id
            base_lesson_id = mode.rsplit("_", 1)[0] if "_" in mode and mode.rsplit("_", 1)[-1].isdigit() else mode
            lesson = LESSONS_DB.get(base_lesson_id)

            if lesson:
                start_time_sec = 52680  # 14:38 (Прибытие в Тверь)
                start_phase = "station_warning" # Сразу готовимся к станции

                incidents_list = lesson.get("incidents", [])
                
                # Если выбрали конкретный под-урок (например, lesson_service_1)
                sub_lesson_idx = int(mode.rsplit("_", 1)[1]) - 1 if "_" in mode and mode.rsplit("_", 1)[-1].isdigit() else None
                
                if sub_lesson_idx is not None and 0 <= sub_lesson_idx < len(incidents_list):
                    target_inc = incidents_list[sub_lesson_idx]["incident_id"]
                    timeline.append({
                        "id": f"lesson_inc_0",
                        "type": "incident",
                        "timeSec": start_time_sec + 30, # Сразу после отправления из Твери
                        "timeStr": "14:38:30",
                        "payload": target_inc
                    })
                else:
                    # Весь урок целиком
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

        # Подбираем пул инцидентов под слабое место
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
            new_state = SCENARIOS_DB[incident_id].get("passenger_state_during", "annoyed")
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
            
            # Добавляем приписку, что сработала защита
            if res_copy.get("mood") in ["annoyed", "drunk"]:
                res_copy["feedback_title"] = "Режим обучения: Штраф отменен"
                res_copy["feedback"] = f"В реальности это решение привело бы к жалобе. Попробуйте еще раз! Анализ: {res_copy.get('feedback', '')}"
        
        return res_copy
