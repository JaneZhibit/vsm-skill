"""
Инструмент подготовки и мастеринга фонового звука поезда ВСМ.
- Срезает раздражающие высокие частоты (стеклопакет 1-го класса).
- Убирает инфразвуковой гул (защита динамиков от хрипа).
- Выравнивает динамику компрессором (сглаживает стук стрелок).
- Делает 100% бесшовный цикл (Seamless Loop) через технику Swap & Crossfade.
"""

from pathlib import Path
import pydub
from pydub import AudioSegment
from pydub.effects import (
    compress_dynamic_range,
    high_pass_filter,
    low_pass_filter,
    normalize,
)
import imageio_ffmpeg

# Автоматическая привязка ffmpeg для Windows/Linux без ручной настройки PATH
pydub.AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()

# ==============================================================================
# ПАРАМЕТРЫ ДЛЯ НАСТРОЙКИ (КРУТИ ЗДЕСЬ)
# ==============================================================================

# Пути к файлам
INPUT_FILE = "../raw_audio/train_ambient.wav"  # Твой исходный файл
OUTPUT_FILE = "../storage/audio/train_ambient.mp3"  # Куда сохранить результат

# 1. ЧАСТОТНЫЕ ФИЛЬТРЫ (EQ)
# Срез верхов: убирает свист кондиционеров и звон рельсов (рекомендуется 2500 - 3500 Гц)
LOW_PASS_CUTOFF_HZ = 3300

# Срез саб-баса: убирает гул, от которого хрипят динамики ноутбуков и телефонов (40 - 60 Гц)
HIGH_PASS_CUTOFF_HZ = 50

# 2. ДИНАМИКА И ГРОМКОСТЬ
# Целевая громкость после нормализации в dBFS (рекомендуется -18..-22 dB для ненавязчивого фона)
TARGET_LUFS_DB = -18.0

# Параметры компрессора (сглаживание перепадов)
COMPRESSOR_THRESHOLD = -16.0  # Порог срабатывания (дБ)
COMPRESSOR_RATIO = 3.0  # Степень сжатия (3:1 для мягкого контроля)
COMPRESSOR_ATTACK = 40.0  # Время атаки (мс)
COMPRESSOR_RELEASE = 180.0  # Время восстановления (мс)

# 3. БЕСШОВНОЕ ЗАЦИКЛИВАНИЕ (LOOP)
# Длина плавного перекрестного наложения стыка (мс). 2000-3000 мс гарантирует 0 щелчков.
CROSSFADE_MS = 2500

# Битрейт итогового MP3 файла (192k дает идеальное качество при весе ~600 Кб на 30 сек)
BITRATE = "192k"

# ==============================================================================


def process_audio():
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)

    if not input_path.exists():
        print(f"❌ Ошибка: входной файл '{INPUT_FILE}' не найден!")
        print(f"Положи исходный файл рядом со скриптом или укажи точный путь.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🎧 Загрузка аудио: {input_path.name}...")
    audio = AudioSegment.from_file(str(input_path))
    duration_sec = len(audio) / 1000.0
    print(f"   Длительность: {duration_sec:.1f} сек, Каналы: {audio.channels}")

    # 1. Применяем фильтры частот
    print(f"🎛️ Применение High-Pass фильтра ({HIGH_PASS_CUTOFF_HZ} Гц)...")
    audio = high_pass_filter(audio, HIGH_PASS_CUTOFF_HZ)

    print(f"🎛️ Применение Low-Pass фильтра ({LOW_PASS_CUTOFF_HZ} Гц)...")
    audio = low_pass_filter(audio, LOW_PASS_CUTOFF_HZ)

    # 2. Мягкая компрессия динамического диапазона
    print(
        f"🗜️ Компрессия (Threshold: {COMPRESSOR_THRESHOLD}dB, Ratio: {COMPRESSOR_RATIO}:1)..."
    )
    audio = compress_dynamic_range(
        audio,
        threshold=COMPRESSOR_THRESHOLD,
        ratio=COMPRESSOR_RATIO,
        attack=COMPRESSOR_ATTACK,
        release=COMPRESSOR_RELEASE,
    )

    # 3. Нормализация и выставление целевой громкости
    print(f"🔊 Подгонка громкости под {TARGET_LUFS_DB} dBFS...")
    audio = normalize(audio)
    # Смещаем громкость от 0 dBFS к целевой
    gain_change = TARGET_LUFS_DB - audio.max_dBFS
    audio = audio.apply_gain(gain_change)

    # 4. Алгоритм создания бесшовной петли (Swap & Crossfade)
    # Разрезаем пополам, меняем куски местами. Тогда начало и конец файла станут
    # бывшей непрерывной серединой записи (0 щелчков на стыке круга),
    # а новый стык в центре сглаживается через crossfade.
    print(f"🔄 Сведение бесшовной петли (Crossfade: {CROSSFADE_MS} мс)...")
    mid = len(audio) // 2
    part_a = audio[:mid]
    part_b = audio[mid:]
    seamless_audio = part_b.append(part_a, crossfade=CROSSFADE_MS)

    # 5. Экспорт
    print(f"💾 Экспорт в {output_path} ({BITRATE})...")
    seamless_audio.export(str(output_path), format="mp3", bitrate=BITRATE)

    file_size_kb = output_path.stat().st_size / 1024
    print(
        f"✅ Готово! Итоговый файл весит: {file_size_kb:.1f} Кб. Бесшовная петля создана."
    )


if __name__ == "__main__":
    process_audio()