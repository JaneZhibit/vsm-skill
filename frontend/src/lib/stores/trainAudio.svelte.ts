import { startAmbient, stopAmbient, playCallBell } from '../utils/audio';

export class TrainAudioStore {
  isAudioMuted = $state<boolean>(true);
  dialogDurationMs = $state<number>(0);

  // Канал 1: Речь пассажира (TTS)
  private passengerVoice: HTMLAudioElement | null = null;

  // Канал 2: Станционные оповещения (Потолочное радио вагона)
  private announcementAudio: HTMLAudioElement | null = null;
  private audioCtx: AudioContext | null = null;
  private announcementGain: GainNode | null = null;
  private announcementFilter: BiquadFilterNode | null = null;

  // Текущее состояние для расчета громкости
  private currentView: 'aisle' | 'seat' = 'aisle';
  private isPassengerSpeaking = false;
  private ambientLoops: Map<string, HTMLAudioElement> = new Map();

  constructor() {
    if (typeof window !== 'undefined') {
      this.initAnnouncementPipeline();
    }
  }

  /** Инициализация Web Audio цепочки для станционного радио */
  private initAnnouncementPipeline(): void {
    try {
      const AudioCtxClass =
        window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!AudioCtxClass) return;

      this.audioCtx = new AudioCtxClass();
      this.announcementAudio = new Audio();
      this.announcementAudio.crossOrigin = 'anonymous';

      const source = this.audioCtx.createMediaElementSource(this.announcementAudio);
      this.announcementFilter = this.audioCtx.createBiquadFilter();
      this.announcementGain = this.audioCtx.createGain();

      // Настройка фильтра: по умолчанию широкий диапазон (проход вагона)
      this.announcementFilter.type = 'lowpass';
      this.announcementFilter.frequency.setValueAtTime(20000, this.audioCtx.currentTime);

      // Цепочка: Аудио -> Потолочный фильтр -> Громкость -> Выход
      source.connect(this.announcementFilter);
      this.announcementFilter.connect(this.announcementGain);
      this.announcementGain.connect(this.audioCtx.destination);
    } catch (e) {
      console.warn('Web Audio API pipeline initialization fallback:', e);
    }
  }

  private ensureAudioContext(): void {
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  /** Расчет целевой громкости и частоты фильтра потолка */
  private applyAcoustics(smoothTime = 0.3): void {
    if (!this.audioCtx || !this.announcementGain || !this.announcementFilter) return;

    const now = this.audioCtx.currentTime;

    // 1. Расчет громкости: в проходе 0.85, у кресла 0.45, при речи пассажира 0.20
    let targetVolume = this.currentView === 'seat' ? 0.45 : 0.85;
    if (this.isPassengerSpeaking) {
      targetVolume = 0.20;
    }

    // 2. Акустический срез частот (имитация динамика в потолке вагона)
    // У кресла звук более глухой и срезанный сверху (3400 Гц), в проходе — чистый (18000 Гц)
    const targetFreq = this.currentView === 'seat' ? 3400 : 18000;

    this.announcementGain.gain.setTargetAtTime(targetVolume, now, smoothTime);
    this.announcementFilter.frequency.setTargetAtTime(targetFreq, now, smoothTime);
  }

  /** Вызывается при переключении камеры (Проход <-> Кресло) */
  public setViewMode(view: 'aisle' | 'seat'): void {
    this.currentView = view;
    this.applyAcoustics(0.25);
  }

  public toggleAudio(): void {
    this.isAudioMuted = !this.isAudioMuted;
    this.ensureAudioContext();
    this.syncAudioPlayback(true, false);
    for (const audio of this.ambientLoops.values()) {
      if (this.isAudioMuted) {
        audio.pause();
      } else {
        audio.play().catch(() => {});
      }
    }
  }

  public unmuteAudio(): void {
    if (this.isAudioMuted) {
      this.isAudioMuted = false;
      this.ensureAudioContext();
      this.syncAudioPlayback(true, false);
      for (const audio of this.ambientLoops.values()) {
        audio.play().catch(() => {});
      }
    }
  }

  public syncAudioPlayback(smooth = true, isPaused = false): void {
    if (this.isAudioMuted || isPaused) {
      stopAmbient(smooth);
    } else {
      startAmbient(smooth);
    }
  }

  public stopAmbient(smooth = true): void {
    stopAmbient(smooth);
  }

  /** Воспроизведение зацикленного эмбиента (плач ребенка и т.п.) */
  public playAmbientLoop(filename: string, volume = 0.4): void {
    if (this.ambientLoops.has(filename)) {
      const existing = this.ambientLoops.get(filename)!;
      if (existing.paused && !this.isAudioMuted) {
        existing.play().catch(() => {});
      }
      return;
    }

    try {
      const audio = new Audio(`/storage/audio/${filename}`);
      audio.loop = true;
      audio.volume = this.isAudioMuted ? 0 : volume;
      this.ambientLoops.set(filename, audio);

      if (!this.isAudioMuted) {
        audio.play().catch((e) => console.warn('Ambient loop autoplay blocked:', e));
      }
    } catch (e) {
      console.warn('Error starting ambient loop:', e);
    }
  }

  /** Остановка зацикленного эмбиента */
  public stopAmbientLoop(filename: string): void {
    const audio = this.ambientLoops.get(filename);
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
      this.ambientLoops.delete(filename);
    }
  }

  public setAmbientDucking(ducked: boolean): void {
    const ambient = document.querySelector('audio');
    if (!ambient || this.isAudioMuted) return;
    ambient.style.transition = 'volume 0.5s ease';
    ambient.volume = ducked ? 0.15 : 0.4;
  }

  /** Плавно глушит текущее станционное оповещение за fadeMs миллисекунд */
  public fadeOutCurrentAnnouncement(fadeMs = 800): Promise<void> {
    return new Promise((resolve) => {
      if (!this.announcementAudio || this.announcementAudio.paused) {
        resolve();
        return;
      }

      if (this.audioCtx && this.announcementGain) {
        const now = this.audioCtx.currentTime;
        const durationSec = fadeMs / 1000;
        this.announcementGain.gain.setValueAtTime(this.announcementGain.gain.value, now);
        this.announcementGain.gain.linearRampToValueAtTime(0.001, now + durationSec);

        setTimeout(() => {
          if (this.announcementAudio) {
            this.announcementAudio.pause();
            this.announcementAudio.currentTime = 0;
          }
          resolve();
        }, fadeMs);
      } else {
        this.announcementAudio.pause();
        resolve();
      }
    });
  }

  /** Воспроизведение станционного оповещения с вытеснением старого */
  public async playVoiceAnnouncement(filename: string): Promise<void> {
    if (this.isAudioMuted) return;
    this.ensureAudioContext();

    // Если прямо сейчас играет старая станция — плавно глушим её за 600 мс!
    await this.fadeOutCurrentAnnouncement(600);

    // Воспроизводим мягкий двухтональный гонг
    playCallBell();

    setTimeout(() => {
      if (!this.announcementAudio) return;

      this.announcementAudio.src = `/storage/audio/announcements/${filename}`;
      this.applyAcoustics(0.1); // Применяем акустику (тише в кресле / чище в проходе)

      this.announcementAudio.play().catch((err) => {
        console.log('Автоплей оповещения заблокирован браузером:', err);
      });
    }, 600);
  }

  /** Воспроизведение реплики пассажира */
  public playPassengerDialog(incidentId: string, archetypeId: string, trait?: string): void {
    if (this.isAudioMuted) return;

    try {
      const primaryUrl = trait
        ? `/storage/audio/dialogs/${incidentId}_${archetypeId}_${trait}.wav`
        : `/storage/audio/dialogs/${incidentId}_${archetypeId}.wav`;

      // Приглушаем фоновое радио вагона на время речи пассажира
      this.isPassengerSpeaking = true;
      this.applyAcoustics(0.2);

      const audio = new Audio(primaryUrl);
      this.passengerVoice = audio;
      audio.volume = 0.95;

      audio.addEventListener('loadedmetadata', () => {
        if (audio.duration && !isNaN(audio.duration)) {
          this.dialogDurationMs = audio.duration * 1000;
        }
      });

      audio.onended = () => {
        this.passengerVoice = null;
        this.dialogDurationMs = 0;
        this.isPassengerSpeaking = false;
        this.applyAcoustics(0.4); // Возвращаем громкость станции
      };

      let hasFallenBack = false;
      audio.onerror = () => {
        if (trait && !hasFallenBack) {
          hasFallenBack = true;
          audio.src = `/storage/audio/dialogs/${incidentId}_${archetypeId}.wav`;
          audio.play().catch(() => {
            this.passengerVoice = null;
            this.dialogDurationMs = 0;
            this.isPassengerSpeaking = false;
            this.applyAcoustics(0.4);
          });
        } else {
          this.passengerVoice = null;
          this.dialogDurationMs = 0;
          this.isPassengerSpeaking = false;
          this.applyAcoustics(0.4);
        }
      };

      audio.play().catch(() => {
        this.passengerVoice = null;
        this.dialogDurationMs = 0;
        this.isPassengerSpeaking = false;
        this.applyAcoustics(0.4);
      });
    } catch {
      this.isPassengerSpeaking = false;
    }
  }
}

export const trainAudio = new TrainAudioStore();
