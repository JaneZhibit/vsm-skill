import json
import base64
import wave
import os
import re
import shutil
import time
import sys
from pathlib import Path
from google import genai

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 1. Пути и настройки
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCisadbtLFJJNm2lUAJT_F5zizgk51WRNg")
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

SCENARIOS_DIR = PROJECT_ROOT / "backend" / "data" / "scenarios"
OUTPUT_DIR = PROJECT_ROOT / "storage" / "audio" / "dialogs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 2. Архетипы пассажиров (голоса)
ARCHETYPES = {
    "male_young": {
        "voice": "Puck",
        "description": "Молодой мужчина 25 лет. Современная естественная речь."
    },
    "female_young": {
        "voice": "Aoede",
        "description": "Молодая девушка 25 лет. Приятный женский тембр."
    },
    "female_elderly": {
        "voice": "Aoede",
        "description": "Пожилая женщина 65+ лет. Говорит медленнее, старческий мягкий или ворчливый голос."
    }
}

# 3. Интонации в зависимости от характера (Trait)
TRAITS_BEHAVIOR = {
    "polite": "Ты вежливый, интеллигентный и воспитанный пассажир. Говори спокойно, доброжелательно, с уважением, без хамства и наездов.",
    "demanding": "Ты требовательный, раздраженный пассажир премиального класса. Говори уверенно, с нажимом, возмущением и напором.",
    "anxious": "Ты тревожный, сильно испуганный пассажир. Говори взволнованно, торопливо, с дрожью в голосе и легкой паникой."
}

# 4. Дополнительные физические состояния
SPECIAL_STATES = {
    "sick": "Тебе физически очень плохо, сильно мутит и кружится голова. Говори тихо, прерывисто, ослабленным голосом.",
    "drunk": "Ты нетрезв. Речь заплетающаяся, смазанная, развязная и громкая."
}


def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def clean_prompt(text: str) -> str:
    """Удаляет внешние кавычки-елочки, оставляя только чистую речь."""
    text = re.sub(r'^.*?«', '', text)
    text = re.sub(r'»$', '', text)
    return text.strip()


def resolve_text_for_passenger(prompt_dict: dict, arch_id: str, trait_id: str) -> str:
    """Иерархический поиск реплики: arch_trait -> trait -> arch -> default."""
    if not isinstance(prompt_dict, dict):
        return str(prompt_dict)

    combo_key = f"{arch_id}_{trait_id}"
    if combo_key in prompt_dict:
        return prompt_dict[combo_key]
    if trait_id in prompt_dict:
        return prompt_dict[trait_id]
    if arch_id in prompt_dict:
        return prompt_dict[arch_id]
    if "default" in prompt_dict:
        return prompt_dict["default"]

    return list(prompt_dict.values())[0] if prompt_dict else ""


def generate_all_dialogs():
    if not API_KEY:
        print("⚠️ ОШИБКА: GEMINI_API_KEY не установлен!")
        return

    if not SCENARIOS_DIR.exists():
        print(f"⚠️ Папка со сценариями {SCENARIOS_DIR} не найдена!")
        return

    client = genai.Client(api_key=API_KEY)
    json_files = sorted(SCENARIOS_DIR.glob("*.json"))

    if not json_files:
        print("⚠️ В папке scenarios нет .json файлов!")
        return

    print(f"🚄 Найдено сценариев: {len(json_files)}")

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Ошибка чтения {json_file.name}: {e}")
            continue

        incident_id = data.get("incident_id") or json_file.stem
        start_step = data.get("start_step", "step_1")
        prompt_field = data.get("steps", {}).get(start_step, {}).get("prompt", {})
        passenger_state = data.get("passenger_state_during", "annoyed")

        print(f"\n==================================================")
        print(f"📝 Обработка: {data.get('title', incident_id)} ({incident_id})")
        print(f"==================================================")

        for arch_id, arch_info in ARCHETYPES.items():
            for trait_id, trait_instruction in TRAITS_BEHAVIOR.items():
                filename = OUTPUT_DIR / f"{incident_id}_{arch_id}_{trait_id}.wav"
                fallback_filename = OUTPUT_DIR / f"{incident_id}_{arch_id}.wav"

                if filename.exists():
                    print(f"⏭️ Пропуск {filename.name} (уже сгенерирован)")
                    continue

                raw_text = resolve_text_for_passenger(prompt_field, arch_id, trait_id)
                base_text = clean_prompt(raw_text)

                if not base_text:
                    continue

                # Формируем эмоциональную установку
                emotion_prompt = trait_instruction
                if passenger_state in SPECIAL_STATES:
                    emotion_prompt += f" ВНИМАНИЕ: {SPECIAL_STATES[passenger_state]}"

                prompt_instruction = (
                    f"You are a professional voice actor. Persona: {arch_info['description']}. "
                    f"Emotional state: {emotion_prompt} "
                    f"TASK: Read the exact Russian text below as this persona with appropriate emotion and intonation. "
                    f"CRITICAL: Speak EXACTLY the words provided word-for-word in Russian. "
                    f"DO NOT add, change, translate, or omit any words. Do not narrate stage directions. "
                    f"Text to perform: \"{base_text}\""
                )

                print(f"🎙️ Запись [{arch_id} | {trait_id}]: «{base_text[:45]}...»")

                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        interaction = client.interactions.create(
                            model="gemini-3.1-flash-tts-preview",
                            input=prompt_instruction,
                            response_format={"type": "audio"},
                            generation_config={
                                "speech_config": [{"voice": arch_info["voice"]}]
                            }
                        )

                        pcm_data = base64.b64decode(interaction.output_audio.data)
                        wave_file(filename, pcm_data)
                        print(f"   ✅ Сохранено: {filename.name}")

                        # Создаем fallback-файл для обратной совместимости
                        if not fallback_filename.exists() or trait_id == "polite":
                            shutil.copyfile(filename, fallback_filename)

                        time.sleep(2.5)  # Защита от лимитов запросов к API
                        break

                    except Exception as e:
                        print(f"   ❌ Попытка {attempt + 1}/{max_retries} для {filename.name}: {e}")
                        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                            wait_time = 10 * (attempt + 1)
                            print(f"   ⏳ Превышен лимит запросов, ожидание {wait_time}с...")
                            time.sleep(wait_time)
                        else:
                            time.sleep(3)


if __name__ == "__main__":
    generate_all_dialogs()