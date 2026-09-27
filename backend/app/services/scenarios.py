import json
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import PROJECT_ROOT, BACKEND_DIR

SCENARIOS_DIR = PROJECT_ROOT / "backend" / "data" / "scenarios"
if not SCENARIOS_DIR.exists():
    SCENARIOS_DIR = BACKEND_DIR / "data" / "scenarios"


def load_scenarios() -> Dict[str, Dict[str, Any]]:
    """Сканирует директорию scenarios/ и подгружает каждый сценарий из отдельного JSON."""
    scenarios_db: Dict[str, Dict[str, Any]] = {}
    if not SCENARIOS_DIR.exists():
        print(f"Warning: Directory {SCENARIOS_DIR} not found. Creating it.")
        SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
        return scenarios_db

    for file_path in SCENARIOS_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                incident_id = data.get("incident_id") or file_path.stem
                scenarios_db[incident_id] = data
        except Exception as e:
            print(f"Error loading {file_path.name}: {e}")

    return scenarios_db


SCENARIOS_DB = load_scenarios()
SCENARIOS = SCENARIOS_DB


def get_scenario_result(incident_id: str, option_id: str) -> Optional[Dict[str, Any]]:
    incident = SCENARIOS_DB.get(incident_id)
    if not incident or "steps" not in incident:
        return None

    if option_id == "opt_timeout":
        return {
            "mood": "annoyed",
            "loyalty_delta": -20,
            "safety_delta": -15,
            "feedback": "Время на принятие решения вышло. Пассажир остался без помощи проводника.",
        }

    for step_data in incident["steps"].values():
        for opt in step_data.get("options", []):
            if opt.get("id") == option_id:
                return opt.get("result") or opt
    return None


def get_frontend_incident_data(incident_id: str) -> Optional[Dict[str, Any]]:
    incident = SCENARIOS_DB.get(incident_id)
    if not incident or "steps" not in incident:
        return None

    frontend_steps = {}
    for step_id, step_data in incident["steps"].items():
        opts = []
        for opt in step_data.get("options", []):
            opt_copy = {
                "id": opt["id"],
                "text": opt["text"],
                "action_type": opt.get("action_type", "click"),
            }
            if "hold_time_ms" in opt:
                opt_copy["hold_time_ms"] = opt["hold_time_ms"]
            if "next_step" in opt:
                opt_copy["next_step"] = opt["next_step"]
            if "result" in opt:
                opt_copy["result"] = opt["result"]
            if "why_correct" in opt:
                opt_copy["why_correct"] = opt["why_correct"]
            if "what_if_wrong" in opt:
                opt_copy["what_if_wrong"] = opt["what_if_wrong"]
            if "expected_rule" in opt:
                opt_copy["expected_rule"] = opt["expected_rule"]
            opts.append(opt_copy)

        frontend_steps[step_id] = {
            "prompt": step_data["prompt"],
            "timer_seconds": step_data.get("timer_seconds", 15),
            "phase": step_data.get("phase", incident.get("phase", "learning")),
            "action_type": step_data.get("action_type", "choice"),
            "expected_rule": step_data.get("expected_rule", ""),
            "options": opts,
        }

    return {
        "incident_id": incident_id,
        "title": incident.get("title", incident_id),
        "phase": incident.get("phase", "learning"),
        "start_step": incident.get("start_step", "step_1"),
        "ambient_audio": incident.get("ambient_audio"),
        "steps": frontend_steps,
    }
