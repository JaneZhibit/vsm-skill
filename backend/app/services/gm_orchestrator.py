import random
from typing import Dict, Any, List, Optional
from app.schemas.passenger import SeatInfo, ActiveIncidentSchema
from app.services.scenarios import SCENARIOS_DB, get_frontend_incident_data
from app.services.gm_timeline import generate_timeline
from app.services.gm_triggers import execute_live_scenario, execute_builtin_trigger

class GameMaster:
    """РћСЂРєРµСЃС‚СЂР°С‚РѕСЂ СЃРѕР±С‹С‚РёР№ Рё РёРЅС†РёРґРµРЅС‚РѕРІ (State Machine)."""
    def __init__(self):
        self.current_mode = "pro"
        self.active_triggers: List[Dict[str, Any]] = []
        self.running_incidents: Dict[str, float] = {}
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
        result = generate_timeline(mode)
        self.current_mode = mode
        if mode.startswith("lesson_"):
            self.active_triggers = []
        else:
            self.init_triggers(mode=mode, start_time=result["start_time"])
        return result

    def process_tick(self, current_time: float, current_speed: Any = 250.0, seats: Optional[List[SeatInfo]] = None) -> List[Dict]:
        if isinstance(current_speed, list):
            seats = current_speed
            current_speed = 250.0
        elif seats is None:
            seats = []

        active_ids_in_cabin = [
            s.active_incident.incident_id if not isinstance(s.active_incident, dict) else s.active_incident["incident_id"]
            for s in seats if s.active_incident
        ]
        
        for inc_id in active_ids_in_cabin:
            if inc_id not in self.running_incidents and inc_id not in self.resolved_incidents:
                self.running_incidents[inc_id] = current_time

        keys_to_remove = [k for k in list(self.running_incidents.keys()) if k not in active_ids_in_cabin]
        for k in keys_to_remove:
            self.resolved_incidents[k] = current_time
            del self.running_incidents[k]

        events_to_fire = []
        remaining = []
        start_time_base = 50400

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
                chance_pct = val if val is not None else 1
                if float(current_speed) > 100 and random.randint(1, 1000) <= (chance_pct * 10):
                    should_fire = True
            elif t_type == "chained":
                parent_id = trig_info.get("parent_id")
                delay = trig_info.get("delay_sec", 0) or 0
                condition = trig_info.get("condition", "ignored")

                if condition == "ignored" and parent_id in self.running_incidents:
                    if current_time - self.running_incidents[parent_id] >= delay:
                        should_fire = True
                elif condition == "resolved" and parent_id in self.resolved_incidents:
                    if current_time - self.resolved_incidents[parent_id] >= delay:
                        should_fire = True

            if should_fire:
                events_to_fire.append(trigger)
                inc_id = sc.get("incident_id", trigger.get("incident_id", trigger.get("id")))
                
                if trigger.get("action") == "custom_live_event" or trigger.get("action") not in ["builtin", "custom_live_event"]:
                    execute_live_scenario(sc, seats)
                elif trigger.get("action") == "builtin":
                    c_time, c_seat = execute_builtin_trigger(trigger, current_time, seats, self.crying_seat_id)
                    if c_time:
                        self.crying_start_time = c_time
                        self.crying_seat_id = c_seat

                if inc_id:
                    self.running_incidents[inc_id] = current_time
            else:
                remaining.append(trigger)

        self.active_triggers = remaining
        return events_to_fire

    def spawn_incident(self, seats: List[SeatInfo], force_incident: Optional[str] = None) -> None:
        """Принудительный спавн инцидента."""
        for seat in seats:
            seat.active_incident = None

        occupied = [s for s in seats if s.is_occupied and s.passenger]
        if not occupied:
            return

        keys = list(SCENARIOS_DB.keys())
        if not force_incident and not keys:
            return
        incident_id = force_incident or random.choice(keys)
        incident_data = get_frontend_incident_data(incident_id)
        scenario = SCENARIOS_DB.get(incident_id, {})
        
        target_arch = scenario.get("target_archetype", "any")
        
        valid_seats = [s for s in occupied if s.passenger.archetype_id == target_arch] if target_arch != "any" else occupied
        if not valid_seats:
            from app.services.passenger_generator import generate_passenger
            target_seat = random.choice(occupied)
            if target_arch != "any":
                target_seat.passenger = generate_passenger(
                    archetype=target_arch,
                    destination=target_seat.passenger.destination,
                    ticket_status=target_seat.passenger.ticket_status,
                    is_boarding=False
                )
        else:
            target_seat = random.choice(valid_seats)

        if incident_data:
            target_seat.active_incident = ActiveIncidentSchema(**incident_data)
            new_state = scenario.get("passenger_state_during", "annoyed")
            target_seat.passenger.state = new_state
            sprite_mood = "neutral" if new_state == "calm" else new_state
            target_seat.passenger.sprite_url = f"/assets/{target_seat.passenger.archetype_id}/{sprite_mood}.png"

    def apply_lesson_protection(self, result: dict) -> dict:
        res_copy = dict(result)
        if self.current_mode.startswith("lesson_"):
            if res_copy.get("loyalty_delta", 0) < 0:
                res_copy["loyalty_delta"] = 0
            if res_copy.get("safety_delta", 0) < 0:
                res_copy["safety_delta"] = 0
            
            if res_copy.get("mood") in ["annoyed", "drunk"]:
                res_copy["feedback_title"] = "Р РµР¶РёРј РѕР±СѓС‡РµРЅРёСЏ: РЁС‚СЂР°С„ РѕС‚РјРµРЅРµРЅ"
                res_copy["feedback"] = f"Р’ СЂРµР°Р»СЊРЅРѕСЃС‚Рё СЌС‚Рѕ СЂРµС€РµРЅРёРµ РїСЂРёРІРµР»Рѕ Р±С‹ Рє Р¶Р°Р»РѕР±Рµ. РџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р·! РђРЅР°Р»РёР·: {res_copy.get('feedback', '')}"
        
        return res_copy

