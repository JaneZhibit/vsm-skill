/**
 * Web Audio API синтезатор звуковых эффектов для тренажера ВСМ.
 * Не требует загрузки внешних аудиофайлов, работает мгновенно и без задержек.
 */

let audioCtx: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null;
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

/** Звук вызова проводника (мягкий двухтональный гонг пассажирского вагона) */
export function playCallBell(): void {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;

    // Первый тон (587.33 Гц - D5)
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(587.33, now);
    gain1.gain.setValueAtTime(0.2, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.9);
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.start(now);
    osc1.stop(now + 0.9);

    // Второй тон (880 Гц - A5) с легкой задержкой
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(880, now + 0.15);
    gain2.gain.setValueAtTime(0.22, now + 0.15);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 1.2);
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.start(now + 0.15);
    osc2.stop(now + 1.2);
  } catch {
    // Безопасный fallback при блокировке автоплея
  }
}

/** Звук верного решения (приятный мажорный аккорд успеха) */
export function playSuccessSound(): void {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6

    notes.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const noteTime = now + idx * 0.08;

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, noteTime);

      gain.gain.setValueAtTime(0.15, noteTime);
      gain.gain.exponentialRampToValueAtTime(0.001, noteTime + 0.6);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(noteTime);
      osc.stop(noteTime + 0.6);
    });
  } catch {
    // Безопасный fallback
  }
}

/** Звук ошибки стандарта (мягкий предупреждающий тон) */
export function playErrorSound(): void {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const notes = [329.63, 293.66]; // E4, D4

    notes.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const noteTime = now + idx * 0.12;

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq, noteTime);

      gain.gain.setValueAtTime(0.12, noteTime);
      gain.gain.exponentialRampToValueAtTime(0.001, noteTime + 0.4);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(noteTime);
      osc.stop(noteTime + 0.4);
    });
  } catch {
    // Безопасный fallback
  }
}

/** Легкий щелчок интерфейса */
export function playClickSound(): void {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(1200, now);
    osc.frequency.exponentialRampToValueAtTime(400, now + 0.04);

    gain.gain.setValueAtTime(0.08, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.04);
  } catch {
    // Безопасный fallback
  }
}

/**
 * Фоновое звуковое окружение поезда (стук колес, аэродинамический гул ВСМ-1)
 */
const AMBIENT_TARGET_VOLUME = 0.4;
let ambientAudio: HTMLAudioElement | null = null;
let fadeInterval: ReturnType<typeof setInterval> | null = null;

function clearAmbientFade(): void {
  if (fadeInterval !== null) {
    clearInterval(fadeInterval);
    fadeInterval = null;
  }
}

function getAmbientAudio(): HTMLAudioElement | null {
  if (typeof window === 'undefined') return null;
  if (!ambientAudio) {
    ambientAudio = new Audio('/storage/audio/train_ambient.mp3');
    ambientAudio.loop = true;
    ambientAudio.volume = AMBIENT_TARGET_VOLUME;
  }
  return ambientAudio;
}

/** Запуск воспроизведения фонового звука с безопасным перехватом ошибки автоплея */
export function startAmbient(smooth = false): void {
  const audio = getAmbientAudio();
  if (!audio) return;
  clearAmbientFade();

  if (!smooth) {
    audio.volume = AMBIENT_TARGET_VOLUME;
    audio.play().catch(() => {});
    return;
  }

  // Плавное нарастание громкости (fade in)
  audio.volume = 0;
  audio.play().catch(() => {});
  const stepTime = 35;
  const steps = 10;
  let step = 0;
  fadeInterval = setInterval(() => {
    step++;
    if (!audio) {
      clearAmbientFade();
      return;
    }
    audio.volume = Math.min(AMBIENT_TARGET_VOLUME, (step / steps) * AMBIENT_TARGET_VOLUME);
    if (step >= steps) {
      clearAmbientFade();
    }
  }, stepTime);
}

/** Остановка фонового звука поезда (с возможностью плавного затухания) */
export function stopAmbient(smooth = false): void {
  const audio = getAmbientAudio();
  if (!audio) return;
  clearAmbientFade();

  if (!smooth || audio.paused) {
    audio.pause();
    return;
  }

  // Плавное затухание громкости (fade out)
  const startVol = audio.volume;
  const stepTime = 35;
  const steps = 10;
  let step = 0;
  fadeInterval = setInterval(() => {
    step++;
    if (!audio) {
      clearAmbientFade();
      return;
    }
    audio.volume = Math.max(0, startVol * (1 - step / steps));
    if (step >= steps) {
      clearAmbientFade();
      audio.pause();
      audio.volume = AMBIENT_TARGET_VOLUME;
    }
  }, stepTime);
}

/** Переключение воспроизведения фонового звука */
export function toggleAmbient(): boolean {
  const audio = getAmbientAudio();
  if (!audio) return false;
  if (audio.paused) {
    startAmbient(true);
    return true;
  } else {
    stopAmbient(true);
    return false;
  }
}

/** Проверка текущего статуса воспроизведения фонового звука */
export function isAmbientPlaying(): boolean {
  const audio = getAmbientAudio();
  if (!audio) return false;
  return !audio.paused;
}
