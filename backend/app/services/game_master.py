import random
from typing import Dict, Any, List, Optional
from app.schemas.passenger import ActiveIncidentSchema, ScenarioStepSchema, SeatInfo
from app.services.scenarios import SCENARIOS_DB, get_frontend_incident_data
from app.services.lessons import LESSONS_DB

class GameMaster:
    """Оркестратор событий и инцидентов (State Machine).
    Обрабатывает тики времени, эмерджентные триггеры, цепные реакции и динамические состояния пассажиров."""

    def __init__(self):
        self.current_mode = "pro"
        self.active_triggers: List[Dict[str, Any]] = []
        # Словарь для отслеживания запущенных событий: { "incident_id": время_старта_сек }
        self.running_incidents: Dict[str, float] = {}
        # Словарь для отслеживания решенных событий: { "incident_id": время_решения_сек }
        self.resolved_incidents: Dict[str, float] = {}
        self.crying_start_time: Optional[float] = None
        self.crying_seat_id: Optional[str] = None
        self.neighbor_complained: bool = False
        self.init_triggers()

    def init_triggers(self, mode: str = "pro", start_time: float = 50400.0) -> None:
        self.current_mode = mode
        self.running_incidents = {}
        self.resolved_incidents = {}
        self.crying_start_time = None
        self.crying_seat_id = None
        self.neighbor_complained = False
        self.active_triggers = []

        if mode.startswith("lesson_"):
            return

        # 1. Загружаем пользовательские живые сценарии из LIVE_SCENARIOS_DB
        try:
            from app.api.v1.endpoints.simulation import LIVE_SCENARIOS_DB
            for inc_id, sc in LIVE_SCENARIOS_DB.items():
                self.active_triggers.append({
                    "id": inc_id,
                    "action": "custom_live_event",
                    "payload": sc
                })
        except Exception as e:
            print(f"Error loading LIVE_SCENARIOS_DB: {e}")

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
                
                self.active_triggers = []
                return {"timeline": timeline, "start_time": start_time_sec, "start_phase": start_phase}

        # РЕЖИМ: PRO или level_*. Начинаем с Москвы (13:50 -> 49800 сек, за 10 минут до отправления)
        start_time_sec = 49800
        start_phase = "initial_round"
        self.init_triggers(mode=mode, start_time=start_time_sec)

        # Контрольные точки для таймлайна (требуются для расписания поездки)
        pool = list(SCENARIOS_DB.keys())
        if pool:
            random.shuffle(pool)
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

    def process_tick(self, current_time: float, current_speed: Any = 250.0, seats: Optional[List[SeatInfo]] = None) -> List[Dict]:
        """Умный тик, обрабатывающий время, скорость, рандом и цепные реакции."""
        if isinstance(current_speed, list):
            seats = current_speed
            current_speed = 250.0
        elif seats is None:
            seats = []

        # 1. Проверяем инциденты в салоне
        active_ids_in_cabin = [
            s.active_incident.incident_id if not isinstance(s.active_incident, dict) else s.active_incident["incident_id"]
            for s in seats if s.active_incident
        ]
        
        # Фиксируем инциденты, появившиеся в вагоне
        for inc_id in active_ids_in_cabin:
            if inc_id not in self.running_incidents and inc_id not in self.resolved_incidents:
                self.running_incidents[inc_id] = current_time

        # Если инцидент был в running, а теперь его нет в салоне -> значит он решен!
        keys_to_remove = [k for k in list(self.running_incidents.keys()) if k not in active_ids_in_cabin]
        for k in keys_to_remove:
            self.resolved_incidents[k] = current_time  # Записываем время решения
            del self.running_incidents[k]

        events_to_fire = []
        remaining = []
        start_time_base = 50400  # 14:00 (Москва)

        for trigger in self.active_triggers:
            sc = trigger.get("payload", {})
            trig_info = sc.get("trigger", {})
            t_type = trig_info.get("type", "time")
            val = trig_info.get("value")
            should_fire = False

            if t_type in ["time", "test"]:
                delay = trig_info.get("delay_sec", trig_info.get("value", 10))
                req_time = start_time_base + (delay if delay is not None else 10)
                if current_time >= req_time:
                    should_fire = True

            elif t_type == "orchestrator":
                delay = trig_info.get("delay_sec", 20)
                req_time = start_time_base + (delay if delay is not None else 20)
                if current_time >= req_time:
                    should_fire = True

            elif t_type == "speed":
                req_speed = val if val is not None else 999
                if float(current_speed) >= req_speed:
                    should_fire = True

            elif t_type == "random":
                # Например, value = 5 (5% шанс каждую секунду, когда скорость > 100)
                chance_pct = val if val is not None else 1
                if float(current_speed) > 100 and random.randint(1, 1000) <= (chance_pct * 10):
                    should_fire = True

            elif t_type == "chained":
                parent_id = trig_info.get("parent_id")
                delay = trig_info.get("delay_sec", 0) or 0
                condition = trig_info.get("condition", "ignored")

                if condition == "ignored":
                    # Срабатывает, если родитель ВСЕ ЕЩЕ ВИСИТ нерешенным спустя delay секунд
                    if parent_id in self.running_incidents:
                        if current_time - self.running_incidents[parent_id] >= delay:
                            should_fire = True

                elif condition == "resolved":
                    # Срабатывает, если родитель БЫЛ РЕШЕН спустя delay секунд после решения
                    if parent_id in self.resolved_incidents:
                        if current_time - self.resolved_incidents[parent_id] >= delay:
                            should_fire = True

            if should_fire:
                events_to_fire.append(trigger)
                inc_id = sc.get("incident_id", trigger.get("incident_id", trigger.get("id")))
                if trigger.get("action") == "custom_live_event":
                    self._execute_live_scenario(sc, seats)
                elif trigger.get("action") == "builtin":
                    self._execute_builtin_trigger(trigger, current_time, seats)
                else:
                    self._execute_live_scenario(sc, seats)

                if inc_id:
                    self.running_incidents[inc_id] = current_time
            else:
                remaining.append(trigger)

        self.active_triggers = remaining
        return events_to_fire

    def _execute_live_scenario(self, scenario: dict, seats: List[SeatInfo]):
        # Ищем подходящего пассажира
        occupied = [s for s in seats if s.is_occupied and s.passenger]
        if not occupied:
            return
        
        target_arch = scenario.get("target_archetype", "any")
        valid_seats = occupied if target_arch == "any" else [s for s in occupied if s.passenger.archetype_id == target_arch]
        
        if not valid_seats:
            valid_seats = occupied  # Фолбэк, если нужного типа нет
            
        # Предпочитаем место без активного инцидента
        free_seats = [s for s in valid_seats if not s.active_incident]
        seat = random.choice(free_seats if free_seats else valid_seats)
        
        # Применяем состояние
        allowed = scenario.get("allowed_moods", [])
        new_state = scenario.get("passenger_state") or (allowed[0] if allowed else "annoyed")
        seat.passenger.state = new_state
        
        # Обновляем спрайт
        seat.passenger.sprite_url = f"/assets/{seat.passenger.archetype_id}/{new_state}.png"
        
        is_passive = scenario.get("is_passive", False)
        phase_str = "passive" if is_passive else "urgent"

        seat.active_incident = ActiveIncidentSchema(
            incident_id=scenario["incident_id"],
            title=scenario.get("title", "Живое событие"),
            phase=phase_str,
            start_step="step_1",
            ambient_audio=scenario.get("ambient_audio"),
            steps={
                "step_1": ScenarioStepSchema(
                    prompt=scenario.get("llm_system_prompt", ""),
                    expected_rule=scenario.get("expected_rule", ""),
                    phase=phase_str,
                    options=[]
                )
            }
        )

    def _execute_builtin_trigger(self, trigger: dict, current_time: float, seats: List[SeatInfo]):
        inc_id = trigger.get("incident_id")
        if not inc_id:
            return
        occupied = [s for s in seats if s.is_occupied and s.passenger]
        if not occupied:
            return

        candidates = [s for s in occupied if not s.active_incident]
        if not candidates:
            candidates = occupied

        if inc_id == "live_crying_child":
            target_seat = next((s for s in candidates if s.passenger.archetype_id == "female_young"), random.choice(candidates))
        elif inc_id == "live_drunk":
            target_seat = next((s for s in candidates if s.passenger.archetype_id == "male_young"), random.choice(candidates))
        elif inc_id == "live_neighbor_complaint":
            crying_seat = next((s for s in seats if s.seat_id == self.crying_seat_id), None)
            if crying_seat:
                neighbor_candidates = [
                    s for s in occupied 
                    if s.seat_id != self.crying_seat_id and not s.active_incident and abs(s.row - crying_seat.row) <= 1
                ]
                target_seat = random.choice(neighbor_candidates) if neighbor_candidates else random.choice(candidates)
            else:
                target_seat = random.choice(candidates)
        else:
            target_seat = random.choice(candidates)

        inc_data = get_frontend_incident_data(inc_id)
        if inc_data:
            inc_data["phase"] = trigger.get("phase", inc_data.get("phase", "urgent"))
            target_seat.active_incident = ActiveIncidentSchema(**inc_data)

            if inc_id == "live_drunk":
                target_seat.passenger.state = "drunk"
                target_seat.passenger.sprite_url = f"/assets/{target_seat.passenger.archetype_id}/drunk.png"
            elif inc_id == "live_crying_child":
                self.crying_start_time = current_time
                self.crying_seat_id = target_seat.seat_id
                target_seat.passenger.state = "annoyed"
                target_seat.passenger.sprite_url = f"/assets/{target_seat.passenger.archetype_id}/annoyed.png"
            else:
                target_seat.passenger.state = "annoyed"
                target_seat.passenger.sprite_url = f"/assets/{target_seat.passenger.archetype_id}/annoyed.png"

    def spawn_incident(self, seats: List[SeatInfo], force_incident: Optional[str] = None) -> None:
        """Назначает инцидент случайному пассажиру."""
        for seat in seats:
            seat.active_incident = None

        occupied = [s for s in seats if s.is_occupied and s.passenger]
        if not occupied:
            return

        target_seat = random.choice(occupied)
        keys = list(SCENARIOS_DB.keys())
        if not force_incident and not keys:
            return
        incident_id = force_incident or random.choice(keys)
        incident_data = get_frontend_incident_data(incident_id)

        if incident_data:
            target_seat.active_incident = ActiveIncidentSchema(**incident_data)
            new_state = SCENARIOS_DB.get(incident_id, {}).get("passenger_state_during", "annoyed")
            target_seat.passenger.state = new_state
            target_seat.passenger.sprite_url = f"/assets/{target_seat.passenger.archetype_id}/{new_state}.png"

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
