import random
from typing import Dict, Any, List, Optional
from app.services.scenarios import SCENARIOS_DB
from app.services.lessons import LESSONS_DB

def generate_timeline(mode: str) -> dict:
    timeline = []
    
    if mode.startswith("lesson_"):
        base_lesson_id = mode.rsplit("_", 1)[0] if "_" in mode and mode.rsplit("_", 1)[-1].isdigit() else mode
        lesson = LESSONS_DB.get(base_lesson_id)
        
        if lesson:
            start_time_sec = 52680
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

    # РЕЖИМ: PRO
    start_time_sec = 49800
    start_phase = "initial_round"
    
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
