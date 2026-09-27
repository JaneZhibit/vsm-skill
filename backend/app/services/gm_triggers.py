import random
from typing import Dict, Any, List, Optional
from app.schemas.passenger import ActiveIncidentSchema, ScenarioStepSchema, SeatInfo
from app.services.scenarios import SCENARIOS_DB, get_frontend_incident_data

def execute_live_scenario(scenario: dict, seats: List[SeatInfo]) -> None:
    occupied = [s for s in seats if s.is_occupied and s.passenger]
    if not occupied:
        return
    
    target_arch = scenario.get("target_archetype", "any")
    valid_seats = occupied if target_arch == "any" else [s for s in occupied if s.passenger.archetype_id == target_arch]
    
    if not valid_seats:
        valid_seats = occupied
        
    free_seats = [s for s in valid_seats if not s.active_incident]
    seat = random.choice(free_seats if free_seats else valid_seats)
    
    allowed = scenario.get("allowed_moods", [])
    new_state = scenario.get("passenger_state") or (allowed[0] if allowed else "annoyed")
    seat.passenger.state = new_state
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

def execute_builtin_trigger(
    trigger: dict, current_time: float, seats: List[SeatInfo], 
    crying_seat_id: Optional[str]
) -> tuple[Optional[float], Optional[str]]:
    """Returns (new_crying_start_time, new_crying_seat_id) if modified."""
    inc_id = trigger.get("incident_id")
    if not inc_id:
        return None, None
    occupied = [s for s in seats if s.is_occupied and s.passenger]
    if not occupied:
        return None, None

    candidates = [s for s in occupied if not s.active_incident]
    if not candidates:
        candidates = occupied

    target_seat = None
    if inc_id == "live_crying_child":
        target_seat = next((s for s in candidates if s.passenger.archetype_id == "female_young"), random.choice(candidates))
    elif inc_id == "live_drunk":
        target_seat = next((s for s in candidates if s.passenger.archetype_id == "male_young"), random.choice(candidates))
    elif inc_id == "live_neighbor_complaint":
        crying_seat = next((s for s in seats if s.seat_id == crying_seat_id), None)
        if crying_seat:
            neighbor_candidates = [
                s for s in occupied 
                if s.seat_id != crying_seat_id and not s.active_incident and abs(s.row - crying_seat.row) <= 1
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
            target_seat.passenger.state = "annoyed"
            target_seat.passenger.sprite_url = f"/assets/{target_seat.passenger.archetype_id}/annoyed.png"
            return current_time, target_seat.seat_id
        else:
            target_seat.passenger.state = "annoyed"
            target_seat.passenger.sprite_url = f"/assets/{target_seat.passenger.archetype_id}/annoyed.png"
    return None, None
