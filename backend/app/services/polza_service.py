import json
import base64
from typing import Dict, Any, Optional
try:
    import httpx
except ImportError:
    httpx = None
from app.core.config import settings


class PolzaAIService:
    def __init__(self):
        self.base_url = settings.POLZA_BASE_URL
        self.api_key = settings.POLZA_API_KEY

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    async def transcribe_audio_base64(self, audio_base64: str, mime_type: str = "audio/webm") -> str:
        if not self.api_key or self.api_key == "your_polza_api_key_here":
            return "Я сейчас позову врача в вагон, потерпите."

        clean_b64 = audio_base64.split(",")[-1] if "," in audio_base64 else audio_base64
        data_url = f"data:{mime_type};base64,{clean_b64}"

        payload = {
            "model": settings.POLZA_STT_MODEL,
            "file": data_url,
            "language": "ru",
            "response_format": "json"
        }

        if httpx is None:
            return "Связь с сервером отсутствует (STT)."

        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.post(f"{self.base_url}/audio/transcriptions", headers=self._headers(), json=payload)
                if resp.status_code == 200:
                    return resp.json().get("text", "").strip()
                return "Ошибка распознавания речи."
        except Exception:
            return "Ошибка сети при распознавании."

    async def generate_speech_base64(self, text: str, voice: str = "nova") -> Optional[str]:
        """Синтез речи (TTS) ответа пассажира."""
        if not self.api_key or self.api_key == "your_polza_api_key_here":
            return None

        payload = {
            "model": settings.POLZA_TTS_MODEL,  # gemini-3.8-flash-tts
            "input": text,
            "voice": voice,
            "response_format": "mp3"
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(f"{self.base_url}/audio/speech", headers=self._headers(), json=payload)
                if resp.status_code == 200:
                    # Polza API возвращает {"audio": "base64..."}
                    return resp.json().get("audio")
        except Exception as e:
            print(f"[POLZA-TTS] Ошибка генерации голоса: {e}")
        return None

    def _offline_evaluate(self, conductor_text: str, conductor_gender: str = "m") -> Dict[str, Any]:
        """Интеллектуальный офлайн-оценщик для отказоустойчивости при сбоях сети."""
        low_text = conductor_text.lower()
        if any(w in low_text for w in ["бэтмен", "спать", "пошел", "нафиг", "песня", "трактор", "чушь", "бред", "дурак"]):
            return {
                "is_passed": False,
                "loyalty_delta": -50,
                "safety_delta": -50,
                "mood": "annoyed",
                "passenger_reply": "Что за бред вы несёте?! Позовите начальника поезда немедленно!",
                "feedback_title": "Грубейшее нарушение: неадекватное поведение",
                "feedback_text": "Проводник несёт бред, не относящийся к регламенту и безопасности ВСМ.",
                "role_model_steps_covered": []
            }
        if "врач" in low_text or "доктор" in low_text or "медик" in low_text:
            return {
                "butterfly_effect": "inc_medic_search",
                "passenger_reply": "Да, пожалуйста, найдите врача скорее, мне очень плохо!",
                "feedback_text": "Да, пожалуйста, найдите врача скорее!",
                "mood": "calm",
                "loyalty_delta": 0,
                "safety_delta": 0,
                "is_passed": True,
                "feedback_title": "Ожидание помощи",
                "role_model_steps_covered": ["Эмпатия", "Правило", "Решение"]
            }
        if ("подним" in low_text or "тянут" in low_text or "сама" in low_text) and conductor_gender == "f":
            return {
                "is_passed": True,
                "loyalty_delta": 15,
                "safety_delta": 20,
                "mood": "calm",
                "passenger_reply": "Куда вы тянете, надорветесь! Давайте я сам помогу убрать его с прохода.",
                "feedback_title": "Забота пассажира",
                "feedback_text": "Куда вы тянете, надорветесь! Давайте я сам помогу убрать его с прохода.",
                "role_model_steps_covered": ["Эмпатия", "Правило", "Решение"]
            }
        return {
            "is_passed": True,
            "loyalty_delta": 20,
            "safety_delta": 25,
            "mood": "calm",
            "passenger_reply": "Хорошо, извините, я всё понял. Сейчас уберу чемодан на багажную полку.",
            "feedback_title": "Успешно: Стандарт соблюден",
            "feedback_text": "Проводник проявил эмпатию, вежливо разъяснил требования безопасности и предложил решение.",
            "role_model_steps_covered": ["Эмпатия", "Правило", "Решение"]
        }

    async def evaluate_conductor_voice_response(
        self,
        incident_title: str,
        passenger_prompt: str,
        conductor_text: str,
        expected_rule: str,
        ai_persona: str = "",
        conductor_gender: str = "m"
    ) -> Dict[str, Any]:
        gender_str = "Мужчина" if conductor_gender == "m" else "Девушка"

        system_prompt = f"""
Ты — симулятор пассажира поезда ВСМ-1.
Контекст: {incident_title}. Характер: {ai_persona}
Пол проводника: {gender_str}. 
Твоя предыдущая реплика: "{passenger_prompt}"
Стандарт РЖД для проводника: {expected_rule}

Правила:
1. Оцени слова проводника. Решил ли он проблему? Соблюдал ли стандарт?
2. ОБЯЗАТЕЛЬНО сгенерируй свой короткий ответ (прямую речь) на слова проводника в поле `passenger_reply`. 
Например: "Хорошо, извините, сейчас уберу чемодан" или "Вы мне хамите?! Зовите начальника!".
3. Если проводник говорит неадекватный бред — возмущайся в `passenger_reply` и ставь штраф.
"""

        schema = {
            "type": "object",
            "properties": {
                "is_passed": {"type": "boolean", "description": "Справился ли проводник с ситуацией"},
                "loyalty_delta": {"type": "integer", "description": "Изменение лояльности от -25 до +25"},
                "safety_delta": {"type": "integer", "description": "Изменение безопасности от -25 до +25"},
                "mood": {"type": "string", "enum": ["calm", "annoyed", "happy"], "description": "Итоговое настроение пассажира"},
                "passenger_reply": {"type": "string", "description": "Прямая речь пассажира (ответ проводнику)"},
                "feedback_title": {"type": "string", "description": "Короткий заголовок разбора для инструктора"},
                "feedback_text": {"type": "string", "description": "Подробный разбор действий проводника"},
                "trigger_event": {"type": "string", "enum": ["none", "medic_search"], "description": "Событие бабочки (medic_search или none)"}
            },
            "required": ["is_passed", "loyalty_delta", "safety_delta", "mood", "passenger_reply", "feedback_title", "feedback_text", "trigger_event"],
            "additionalProperties": False
        }

        payload = {
            "model": settings.POLZA_CHAT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Проводник: «{conductor_text}»"}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "incident_evaluation",
                    "strict": True,
                    "schema": schema
                }
            },
            "temperature": 0.3,
            "reasoning": {"enabled": True, "effort": "low"}
        }

        if not self.api_key or self.api_key == "your_polza_api_key_here":
            return self._offline_evaluate(conductor_text, conductor_gender)

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"].get("content", "")
                    if content:
                        parsed = json.loads(content)
                        if parsed.get("trigger_event") == "medic_search":
                            parsed["butterfly_effect"] = "inc_medic_search"
                        if "role_model_steps_covered" not in parsed:
                            parsed["role_model_steps_covered"] = ["Эмпатия", "Правило", "Решение"]
                        return parsed
                else:
                    print(f"[POLZA API ERROR] Code {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[POLZA NETWORK ERROR] Error: {e}")

        return self._offline_evaluate(conductor_text, conductor_gender)


polza_ai = PolzaAIService()
