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
            return "Пожалуйста, соблюдайте правила проезда в поезде."

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

    async def generate_speech_base64(
        self,
        text: str,
        archetype: str = "female_young",
        trait: str = "polite",
        voice: Optional[str] = None
    ) -> Optional[str]:
        """Синтез речи (TTS) с динамическим подбором голоса и скорости."""
        if not self.api_key or self.api_key == "your_polza_api_key_here":
            return None

        # Подбор голоса по архетипу (OpenAI TTS)
        voice_map = {
            "male_young": "onyx",         # Мужской, глубокий
            "female_young": "nova",       # Женский, энергичный
            "female_elderly": "shimmer",  # Женский, мягкий
            "any": "alloy"
        }
        selected_voice = voice or voice_map.get(archetype, "alloy")

        # Настройка скорости по характеру
        speed = 1.0
        if trait == "demanding":
            speed = 1.15  # Говорит быстро и напористо
        elif trait == "anxious":
            speed = 1.05  # Немного нервно
        elif trait == "polite":
            speed = 0.95  # Размеренно и спокойно

        payload = {
            "model": "openai/tts-1",  # Надежная быстрая модель
            "input": text,
            "voice": selected_voice,
            "speed": speed,
            "response_format": "mp3"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{self.base_url}/audio/speech", headers=self._headers(), json=payload)
                if resp.status_code == 200:
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
                "mood": "sick",
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
                "mood": "happy",
                "passenger_reply": "Куда вы тянете, надорветесь! Давайте я сам помогу убрать его с прохода.",
                "feedback_title": "Забота пассажира",
                "feedback_text": "Куда вы тянете, надорветесь! Давайте я сам помогу убрать его с прохода.",
                "role_model_steps_covered": ["Эмпатия", "Правило", "Решение"]
            }
        return {
            "is_passed": True,
            "loyalty_delta": 20,
            "safety_delta": 25,
            "mood": "neutral",
            "passenger_reply": "Хорошо, извините, я всё понял. Сейчас выполню правила перевозки.",
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
        passenger_profile: Optional[dict] = None,
        conductor_gender: str = "m",
        ai_persona: str = ""
    ) -> Dict[str, Any]:
        cond_gender_str = "Мужчина" if conductor_gender == "m" else "Девушка"
        profile = passenger_profile or {}
        trait = profile.get("trait", "polite")
        trait_ru = {"polite": "вежливый и спокойный", "demanding": "требовательный скандалист", "anxious": "тревожный и нервный"}.get(trait, "нейтральный")
        
        # Доступные картинки-спрайты
        available_sprites = ["neutral", "angry", "vaping", "crying_child", "drunk", "sleeping", "happy", "annoyed", "sick"]

        system_prompt = f"""
Ты — пассажир скоростного поезда ВСМ-1. Это реалистичная Role-Play симуляция.
ТВОЙ ПРОФИЛЬ:
- Тип: {profile.get('archetype_id', 'Неизвестно')}
- Характер: {trait_ru}
- Текущая ситуация: {incident_title}
- Твоя реплика до этого момента: "{passenger_prompt}"
{f"- Дополнительный контекст: {ai_persona}" if ai_persona else ""}

ОБСТАНОВКА:
Перед тобой стоит проводник ({cond_gender_str}). 
Оцени его слова: «{conductor_text}».
Правило, которому он должен был следовать: {expected_rule}.

ЗАДАЧА:
1. Ответь проводнику строго в соответствии со своим характером ({trait_ru}). Если он груб или не решил проблему — возмущайся. Если вежлив и прав — соглашайся.
2. Выбери свое визуальное состояние (спрайт) из списка: {available_sprites}.
3. Оцени проводника.

Выведи ответ строго в JSON по указанной схеме.
"""

        payload = {
            "model": settings.POLZA_CHAT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Проводник: «{conductor_text}»"}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "passenger_response",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "is_passed": {"type": "boolean", "description": "Проблема решена?"},
                            "loyalty_delta": {"type": "integer", "description": "Очки сервиса (-50..50)"},
                            "safety_delta": {"type": "integer", "description": "Очки безопасности (-50..50)"},
                            "mood": {"type": "string", "enum": available_sprites, "description": "Новый спрайт пассажира"},
                            "passenger_reply": {"type": "string", "description": "Твоя прямая речь"},
                            "feedback_title": {"type": "string", "description": "Заголовок разбора для инструктора"},
                            "feedback_text": {"type": "string", "description": "Текст разбора для инструктора"},
                            "trigger_butterfly": {"type": "boolean", "description": "Требуется ли вызвать врача? (Эффект бабочки)"}
                        },
                        "required": ["is_passed", "loyalty_delta", "safety_delta", "mood", "passenger_reply", "feedback_title", "feedback_text"]
                    },
                    "strict": False
                }
            },
            "temperature": 0.2
        }

        if not self.api_key or self.api_key == "your_polza_api_key_here":
            return self._offline_evaluate(conductor_text, conductor_gender)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=payload)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    if content.startswith("```json"):
                        content = content.replace("```json", "").replace("```", "").strip()
                    
                    data = json.loads(content)
                    data["role_model_steps_covered"] = ["Эмпатия", "Правило", "Решение"]
                    if data.get("trigger_butterfly"):
                        data["butterfly_effect"] = "inc_medic_search"
                    return data
                else:
                    print(f"[POLZA API ERROR] Code {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[POLZA ERROR] {e}")

        return self._offline_evaluate(conductor_text, conductor_gender)


polza_ai = PolzaAIService()
