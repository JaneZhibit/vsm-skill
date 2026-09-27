from typing import Optional, Any, Dict
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.db_queries import log_action
from app.api.v1.endpoints.users import get_current_user
from app.schemas.passenger import CabinManifestResponse
from app.services.trip_engine import trip_manager
from app.services.scenarios import get_scenario_result, SCENARIOS_DB
from app.services.polza_service import polza_ai

router = APIRouter()


class SpawnSpecificRequest(BaseModel):
    incident_id: str


@router.post("/trip/spawn-specific", response_model=CabinManifestResponse)
async def trigger_specific_incident(
        payload: SpawnSpecificRequest,
        user: Dict[str, Any] = Depends(get_current_user),
):
    from fastapi import HTTPException
    engine = trip_manager.get_trip(user["id"])
    manifest, success = engine.spawn_incident(force_incident=payload.incident_id)
    if not success:
        raise HTTPException(status_code=400, detail="Incident already spawned or no seats available")
    return manifest


@router.post("/trip/spawn-random", response_model=CabinManifestResponse)
async def trigger_random_incident(user: Dict[str, Any] = Depends(get_current_user)):
    from fastapi import HTTPException
    engine = trip_manager.get_trip(user["id"])
    manifest, success = engine.spawn_incident()
    if not success:
        raise HTTPException(status_code=400, detail="No available incidents or seats")
    return manifest


class ResolveIncidentRequest(BaseModel):
    incident_id: str
    option_id: str


@router.post("/resolve-incident")
async def resolve_simulation_incident(payload: ResolveIncidentRequest,
                                      user: Dict[str, Any] = Depends(get_current_user)):
    scenario_result = get_scenario_result(payload.incident_id, payload.option_id)
    if not scenario_result:
        raise HTTPException(status_code=400, detail="РќРµРІРµСЂРЅС‹Р№ ID РёРЅС†РёРґРµРЅС‚Р° РёР»Рё РѕРїС†РёРё")

    engine = trip_manager.get_trip(user["id"])
    protected_result = engine.game_master.apply_lesson_protection(scenario_result)

    incident_meta = SCENARIOS_DB.get(payload.incident_id, {})
    step1 = incident_meta.get("steps", {}).get("step_1", {})
    chosen_opt = next((o for o in step1.get("options", []) if o.get("id") == payload.option_id), {})
    if chosen_opt.get("next_step") == "trigger_medic" or protected_result.get("butterfly_effect") == "inc_medic_search":
        engine.game_master.spawn_incident(engine.passenger_manager.seats, force_incident="inc_medic_search")

    updated_user = await log_action(
        user_id=user["id"],
        incident_id=payload.incident_id,
        option_id=payload.option_id,
        loyalty_delta=protected_result["loyalty_delta"],
        safety_delta=protected_result.get("safety_delta", 0),
        feedback=protected_result.get("feedback", ""),
    )

    engine.resolve_incident(payload.incident_id, protected_result)

    return {
        "status": "resolved",
        "user": updated_user,
        "incident_result": protected_result,
        "manifest": engine.get_manifest()
    }


class VoiceResolveRequest(BaseModel):
    incident_id: str
    audio_base64: Optional[str] = None
    conductor_text: Optional[str] = None
    passenger_prompt: Optional[str] = ""
    expected_rule: Optional[str] = ""


@router.post("/trip/voice-resolve")
async def resolve_voice_incident(
        payload: VoiceResolveRequest,
        user: Dict[str, Any] = Depends(get_current_user),
):
    conductor_speech = ""
    if payload.audio_base64:
        conductor_speech = await polza_ai.transcribe_audio_base64(payload.audio_base64, "audio/webm")
    elif payload.conductor_text:
        conductor_speech = payload.conductor_text.strip()

    if not conductor_speech:
        return {
            "status": "empty_speech",
            "incident_result": {
                "dialog_status": "continue",
                "loyalty_delta": 0,
                "safety_delta": 0,
                "mood": "annoyed",
                "passenger_reply": "Р’С‹ С‡С‚Рѕ-С‚Рѕ СЃРєР°Р·Р°Р»Рё? РЇ РЅРµ СЂР°СЃСЃР»С‹С€Р°Р».",
                "feedback_title": "Р“РѕР»РѕСЃ РЅРµ СЂР°СЃРїРѕР·РЅР°РЅ",
                "feedback": "РџРѕРІС‚РѕСЂРёС‚Рµ С‡РµС‚С‡Рµ.",
            }
        }

    engine = trip_manager.get_trip(user["id"])
    incident_meta = SCENARIOS_DB.get(payload.incident_id, {})
    ai_persona = incident_meta.get("ai_persona", "")
    allowed_moods = incident_meta.get("allowed_moods")

    active_seat = next((s for s in engine.passenger_manager.seats if s.active_incident and (
            (isinstance(s.active_incident, dict) and s.active_incident.get("incident_id") == payload.incident_id) or
            (getattr(s.active_incident, "incident_id", None) == payload.incident_id)
    )), None)

    if not active_seat:
        active_seat = next((s for s in engine.passenger_manager.seats if s.seat_id == payload.incident_id), None)
        incident_title = "РћР±С‹С‡РЅР°СЏ РїРѕРµР·РґРєР°, РїСЂРѕРІРµСЂРєР° Р±РёР»РµС‚РѕРІ РёР»Рё СЃРІРѕР±РѕРґРЅС‹Р№ СЂР°Р·РіРѕРІРѕСЂ"
    else:
        incident_title = incident_meta.get("title", payload.incident_id)

    passenger_profile = active_seat.passenger.model_dump() if (active_seat and active_seat.passenger) else {}
    history = getattr(active_seat.passenger, "dialog_history", []) if (active_seat and active_seat.passenger) else []

    eval_result = await polza_ai.evaluate_conductor_voice_response(
        incident_title=incident_title,
        passenger_prompt=payload.passenger_prompt,
        conductor_text=conductor_speech,
        expected_rule=payload.expected_rule or "РЎРўРћ Р Р–Р” 03.011 (Р’РµР¶Р»РёРІРѕРµ РѕР±С‰РµРЅРёРµ СЃ РїР°СЃСЃР°Р¶РёСЂР°РјРё)",
        passenger_profile=passenger_profile,
        conductor_gender=user.get("gender", "m"),
        ai_persona=ai_persona,
        allowed_moods=allowed_moods,
        dialog_history=history
    )
    eval_result = engine.game_master.apply_lesson_protection(eval_result)

    passenger_reply_text = eval_result.get("passenger_reply", "")
    if active_seat and active_seat.passenger:
        if not hasattr(active_seat.passenger, "dialog_history") or active_seat.passenger.dialog_history is None:
            active_seat.passenger.dialog_history = []
        active_seat.passenger.dialog_history.append({"role": "user", "content": f"РџСЂРѕРІРѕРґРЅРёРє: В«{conductor_speech}В»"})
        active_seat.passenger.dialog_history.append(
            {"role": "assistant", "content": f"РџР°СЃСЃР°Р¶РёСЂ: В«{passenger_reply_text}В»"})
        if len(active_seat.passenger.dialog_history) > 6:
            active_seat.passenger.dialog_history = active_seat.passenger.dialog_history[-6:]

    passenger_audio_b64 = None
    if passenger_reply_text:
        archetype = passenger_profile.get("archetype_id", "female_young")
        trait = passenger_profile.get("trait", "polite")
        passenger_audio_b64 = await polza_ai.generate_speech_base64(passenger_reply_text, archetype, trait)

    if "butterfly_effect" in eval_result:
        engine.game_master.spawn_incident(engine.passenger_manager.seats,
                                          force_incident=eval_result["butterfly_effect"])
        engine.resolve_incident(payload.incident_id, eval_result)
        return {
            "status": "resolved",
            "transcription": conductor_speech,
            "manifest": engine.get_manifest(),
            "incident_result": {
                "dialog_status": "resolved",
                "loyalty_delta": 0,
                "safety_delta": 0,
                "mood": "sick",
                "passenger_reply": passenger_reply_text,
                "passenger_audio_base64": passenger_audio_b64,
                "feedback": f"РџР°СЃСЃР°Р¶РёСЂ РѕС‚РІРµС‚РёР»: В«{passenger_reply_text}В». Р’С‹ РїРµСЂРµС€Р»Рё Рє РїРѕРёСЃРєСѓ РїРѕРјРѕС‰Рё.",
                "feedback_title": "Р­С„С„РµРєС‚ Р±Р°Р±РѕС‡РєРё",
                "transcription": conductor_speech,
            },
        }

    # РќРћР’РђРЇ Р›РћР“РРљРђ РњРќРћР“РћРЁРђР“РћР’РћР“Рћ Р”РРђР›РћР“Рђ
    dialog_status = eval_result.get("dialog_status", "resolved")

    if dialog_status == "continue":
        # РћР±РЅРѕРІР»СЏРµРј С‚РѕР»СЊРєРѕ Р»РёС†Рѕ РїР°СЃСЃР°Р¶РёСЂР° Рё Р»РѕРіРёСЂСѓРµРј РїРѕРїС‹С‚РєСѓ, РЅРѕ РќР• Р·Р°РєСЂС‹РІР°РµРј РёРЅС†РёРґРµРЅС‚
        if active_seat and active_seat.passenger:
            active_seat.passenger.state = eval_result.get("mood", active_seat.passenger.state)
            sprite_mood = "neutral" if active_seat.passenger.state == "calm" else active_seat.passenger.state
            active_seat.passenger.sprite_url = f"/assets/{active_seat.passenger.archetype_id}/{sprite_mood}.png"

        updated_user = await log_action(
            user_id=user["id"],
            incident_id=payload.incident_id,
            option_id="voice_response_continue",
            loyalty_delta=eval_result.get("loyalty_delta", 0),
            safety_delta=eval_result.get("safety_delta", 0),
            feedback=eval_result.get("feedback_text", ""),
        )
        return {
            "status": "continue",
            "transcription": conductor_speech,
            "user": updated_user,
            "manifest": engine.get_manifest(),
            "incident_result": {
                "dialog_status": "continue",
                "loyalty_delta": eval_result.get("loyalty_delta", 0),
                "safety_delta": eval_result.get("safety_delta", 0),
                "mood": eval_result.get("mood", "calm"),
                "passenger_reply": passenger_reply_text,
                "passenger_audio_base64": passenger_audio_b64,
                "feedback": eval_result.get("feedback_text", "РџР°СЃСЃР°Р¶РёСЂ РѕР¶РёРґР°РµС‚ Р°СЂРіСѓРјРµРЅС‚РѕРІ."),
                "feedback_title": eval_result.get("feedback_title", "РџСЂРѕРґРѕР»Р¶РµРЅРёРµ РґРёР°Р»РѕРіР°"),
                "role_model_steps": eval_result.get("role_model_steps_covered", []),
                "transcription": conductor_speech,
            }
        }
    else:
        # Р”РёР°Р»РѕРі Р·Р°РІРµСЂС€РµРЅ (СѓСЃРїРµС… РёР»Рё СЃРєР°РЅРґР°Р»)
        updated_user = await log_action(
            user_id=user["id"],
            incident_id=payload.incident_id,
            option_id="voice_response_final",
            loyalty_delta=eval_result.get("loyalty_delta", 0),
            safety_delta=eval_result.get("safety_delta", 0),
            feedback=eval_result.get("feedback_text", ""),
        )
        engine.resolve_incident(payload.incident_id, eval_result)

        return {
            "status": "resolved",
            "transcription": conductor_speech,
            "user": updated_user,
            "manifest": engine.get_manifest(),
            "incident_result": {
                "dialog_status": dialog_status,
                "loyalty_delta": eval_result.get("loyalty_delta", 0),
                "safety_delta": eval_result.get("safety_delta", 0),
                "mood": eval_result.get("mood", "calm"),
                "passenger_reply": passenger_reply_text,
                "passenger_audio_base64": passenger_audio_b64,
                "feedback": eval_result.get("feedback_text", "РћС†РµРЅРµРЅРѕ."),
                "feedback_title": eval_result.get("feedback_title", "РђРЅР°Р»РёР· РѕС‚РІРµС‚Р°"),
                "role_model_steps": eval_result.get("role_model_steps_covered", []),
                "transcription": conductor_speech,
            },
        }
