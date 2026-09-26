import json
import base64
import os
import re
import shutil
import time
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import httpx
except ImportError:
    print("❌ Пожалуйста, установите httpx: pip install httpx")
    sys.exit(1)

# Убедитесь, что в консоли перед запуском установлен set POLZA_API_KEY=...
API_KEY = os.environ.get("POLZA_API_KEY", "pza_BpKlAcgmxzox5c3CJ5Idn4mboEwiQhSJ")
BASE_URL = "https://polza.ai/api/v1"
MODEL = "google/gemini-3.8-flash-tts"

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

SCENARIOS_DIR = PROJECT_ROOT / "backend" / "data" / "scenarios"
OUTPUT_DIR = PROJECT_ROOT / "storage" / "audio" / "dialogs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Единый реестр голосов Gemini 3.8 Flash TTS для проекта
ARCHETYPES = {
    "male_young": {
        "voice": "Puck",      # Оптимистичный, живой (Молодой парень)
        "desc": "Молодой мужчина"
    },
    "female_young": {
        "voice": "Leda",      # Юный, молодёжный (Девушка)
        "desc": "Девушка"
    },
    "female_elderly": {
        "voice": "Sulafat",   # Тёплый, уютный (Бабушка)
        "desc": "Пожилая женщина"
    }
}


# Альтернативные голоса Gemini для справки:
# Zephyr — Bright, Fenrir — Excitable, Charon — Informative,
# Aoede — Light, Leda — Youthful, Sulafat — Warm


def clean_prompt(text: str) -> str:
    """
    Очищает текст от служебных элементов и инструкций.

    Gemini 3.8 Flash TTS читает ВСЁ дословно, поэтому:
    - Убираем обрамляющие кавычки-ёлочки
    - Убираем ремарки в квадратных/круглых скобках
    - Убираем служебные префиксы типа "Скажи ..."
    - Оставляем только чистый текст реплики
    """
    if not text:
        return ""

    # Убираем обрамляющие кавычки-ёлочки
    text = re.sub(r'^.*?«', '', text)
    text = re.sub(r'»$', '', text)

    # Убираем ремарки в скобках (например, "(смеётся)", "[вздыхает]")
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)

    # Убираем служебные инструкции в начале строки
    text = re.sub(r'^(Скажи|Произнеси|Скажите|Произнесите)\s+', '', text, flags=re.IGNORECASE)

    # Убираем множественные пробелы и переносы
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def resolve_text_for_passenger(prompt_dict: dict, arch_id: str, trait_id: str) -> str:
    """Извлекает текст реплики для заданного архетипа и характера."""
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
    if not API_KEY or API_KEY == "your_polza_api_key_here":
        print("⚠️ ОШИБКА: POLZA_API_KEY не установлен!")
        return

    json_files = sorted(SCENARIOS_DIR.glob("*.json"))
    print(f"🚄 Найдено сценариев: {len(json_files)}")

    overwrite = os.environ.get("OVERWRITE", "0") == "1" or "--overwrite" in sys.argv
    arch_filter = [arg for arg in sys.argv[1:] if arg in ARCHETYPES]
    active_archetypes = {k: v for k, v in ARCHETYPES.items() if not arch_filter or k in arch_filter}
    if overwrite:
        print("🔄 Режим перезаписи: существующие файлы будут обновлены.")
    if arch_filter:
        print(f"🎯 Фильтр по архетипам: {list(active_archetypes.keys())}")

    with httpx.Client(timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            incident_id = data.get("incident_id", json_file.stem)
            start_step = data.get("start_step", "step_1")
            prompt_field = data.get("steps", {}).get(start_step, {}).get("prompt", {})

            for arch_id, arch_info in active_archetypes.items():
                for trait_id in ["polite", "demanding", "anxious"]:
                    filename = OUTPUT_DIR / f"{incident_id}_{arch_id}_{trait_id}.wav"
                    fallback_filename = OUTPUT_DIR / f"{incident_id}_{arch_id}.wav"

                    if filename.exists() and not overwrite:
                        continue

                    raw_text = resolve_text_for_passenger(prompt_field, arch_id, trait_id)
                    base_text = clean_prompt(raw_text)

                    if not base_text:
                        print(f"⏭️ Пропуск [{arch_id} | {trait_id}]: пустой текст")
                        continue

                    # Формируем запрос для Gemini 3.8 Flash TTS
                    # ВАЖНО: поле "input" — это ДОСЛОВНЫЙ текст для озвучки.
                    # Стиль передаётся отдельно (если Polza AI поддерживает).
                    payload = {
                        "model": MODEL,
                        "input": base_text,
                        "voice": arch_info["voice"],
                        "response_format": "wav",
                    }

                    # Опционально: стиль подачи (если Polza AI поддерживает)
                    # Раскомментируйте, если API принимает этот параметр:
                    # if "style" in arch_info:
                    #     payload["style"] = arch_info["style"]

                    print(f"🎙️ Запись [{arch_id} | {trait_id} | {arch_info['voice']}]: «{base_text[:35]}...»")

                    try:
                        resp = client.post(
                            f"{BASE_URL}/audio/speech",
                            headers=headers,
                            json=payload
                        )
                        if resp.status_code == 200:
                            b64_audio = resp.json().get("audio")
                            if b64_audio:
                                with open(filename, "wb") as out_f:
                                    out_f.write(base64.b64decode(b64_audio))
                                print(f"   ✅ Сохранено: {filename.name}")

                                # Создаём fallback без указания характера
                                if not fallback_filename.exists() or trait_id == "polite" or overwrite:
                                    shutil.copyfile(filename, fallback_filename)
                                    print(f"   📋 Fallback: {fallback_filename.name}")
                            else:
                                print(f"   ⚠️ Пустой аудиоответ")
                        else:
                            print(f"   ❌ Ошибка {resp.status_code}: {resp.text[:200]}")
                    except Exception as e:
                        print(f"   ❌ Сбой сети: {e}")

                    time.sleep(1)  # Защита от Rate Limit


if __name__ == "__main__":
    generate_all_dialogs()