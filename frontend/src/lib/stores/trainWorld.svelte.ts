import { apiFetch } from '../services/api';
import {
  ROUTE_CHECKPOINTS,
  timeStringToSeconds,
  secondsToTimeString,
  DEPARTURE_SECONDS,
  ARRIVAL_SECONDS,
  type RouteCheckpoint,
} from '../config/routeConfig';
import { playCallBell, playErrorSound } from '../utils/audio';

import { trainAudio } from './trainAudio.svelte';
import {
  conductorState,
  type ShiftPhase,
  type ConductorProfile,
  type ConductorSkills,
} from './conductorState.svelte';
import { physicsState, type MovementStatus } from './trainPhysics.svelte';
import { cabinState, type PassengerMood, type CabinView } from './cabinState.svelte';
import { convertSeatInfoToPassengerSeat, type PassengerSeat } from '../config/cabinConfig';

// Реэкспорт типов, чтобы UI-компоненты не сломались
export type {
  ShiftPhase,
  ConductorProfile,
  ConductorSkills,
  MovementStatus,
  PassengerMood,
  CabinView,
  PassengerSeat,
};

export type TimelineEventType = 'station_arrival' | 'incident' | 'routine';

export interface TimelineEvent {
  id: string;
  timeStr: string; // "HH:mm" или "HH:mm:ss"
  timeSec: number; // Вычислим при старте
  type: TimelineEventType;
  payload?: any; // ID инцидента или индекс станции
  triggered: boolean;
}



export class TrainWorldStore {
  // --- ЛОКАЛЬНЫЕ ДАННЫЕ ОРКЕСТРАТОРА ---
  tripMode = $state<string>('pro');
  isPhaseTransitioning = $state<boolean>(false); // Для красивого экрана загрузки/перехода
  timeSkippedText = $state<string>('');
  activeTimeline = $state<TimelineEvent[]>([]);
  reactionTimeLeft = $state<number>(0); // <--- ДОБАВЛЕН ТАЙМЕР РЕАКЦИИ

  // --- МИНИ-ИГРЫ: ПРИЕМКА И СДАЧА ВАГОНА ---
  preTripChecks = $state({ fireExtinguisher: false, climate: false, toilet: false });
  postTripItems = $state([
    { id: 'trash1', type: 'trash', top: '75%', left: '35%', icon: '🥤', isFound: false },
    { id: 'trash2', type: 'trash', top: '82%', left: '60%', icon: '🗞️', isFound: false },
    { id: 'lost1', type: 'lost', top: '65%', left: '25%', icon: '🌂', isFound: false }, // Забытый зонт на кресле
  ]);

  get isPreTripDone() {
    return this.preTripChecks.fireExtinguisher && this.preTripChecks.climate && this.preTripChecks.toilet;
  }

  get isPostTripDone() {
    return this.postTripItems.every(item => item.isFound);
  }

  lastProcessedStationIndex = $state<number>(0);
  warnedStationIndices = $state<number[]>([]);
  announcedStationIndices = $state<number[]>([]);
  hasPlayedWelcome = $state<boolean>(false);
  hasPlayedFinalSpb = $state<boolean>(false);
  
  stationToast = $state<{ title: string; subtitle: string } | null>(null);
  private stationToastTimer: ReturnType<typeof setTimeout> | null = null;
  
  private lastFrameTime = 0;
  private animationFrameId: number | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.lastFrameTime = performance.now();
      cabinState.loadCabinManifest().then(() => {
        this.fetchTripState();
      });
      this.startLoop();
      setInterval(() => { if (!this.isPaused) this.syncTripState(); }, 5000);
    }
  }

  public abortTrip(): void {
    this.activeTimeline = [];
    physicsState.isPaused = true;
    trainAudio.stopAmbient(true); // Плавно гасим звук поезда
  }

  // --- ДЕЛЕГАТЫ: AUDIO ---
  get isAudioMuted() { return trainAudio.isAudioMuted; }
  set isAudioMuted(val) { trainAudio.isAudioMuted = val; }
  public toggleAudio() { trainAudio.toggleAudio(); }
  public unmuteAudio() { trainAudio.unmuteAudio(); }
  public syncAudioPlayback(smooth = true) { trainAudio.syncAudioPlayback(smooth, this.isPaused); }
  public playPassengerDialog(incidentId: string, archetypeId: string, trait?: string) {
    trainAudio.playPassengerDialog(incidentId, archetypeId, trait);
  }

  // --- ДЕЛЕГАТЫ: CONDUCTOR ---
  get conductorProfile() { return conductorState.conductorProfile; }
  set conductorProfile(val) { conductorState.conductorProfile = val; }
  get skills() { return conductorState.skills; }
  set skills(val) { conductorState.skills = val; }
  get loyaltyScore() { return conductorState.loyaltyScore; }
  set loyaltyScore(val) { conductorState.loyaltyScore = val; }
  get safetyScore() { return conductorState.safetyScore; }
  set safetyScore(val) { conductorState.safetyScore = val; }
  get shiftPhase() { return conductorState.shiftPhase; }
  set shiftPhase(val) { conductorState.shiftPhase = val; }
  get isEmergencyInterrupted() { return conductorState.isEmergencyInterrupted; }
  set isEmergencyInterrupted(val) { conductorState.isEmergencyInterrupted = val; }
  get emergencyMessage() { return conductorState.emergencyMessage; }
  set emergencyMessage(val) { conductorState.emergencyMessage = val; }
  get overallReadiness() { return conductorState.overallReadiness; }
  get weakestSkill() { return conductorState.weakestSkill; }
  public interrupt(reason = 'Экстренное прерывание') { physicsState.setRealTime(); conductorState.triggerEmergency(reason); }

  // --- ДЕЛЕГАТЫ: PHYSICS ---
  get timeSeconds() { return physicsState.timeSeconds; }
  set timeSeconds(val) { physicsState.timeSeconds = val; }
  get speed() { return physicsState.speed; }
  set speed(val) { physicsState.speed = val; }
  get isPaused() { return physicsState.isPaused; }
  set isPaused(val) { physicsState.isPaused = val; }
  get timeScale() { return physicsState.timeScale; }
  set timeScale(val) { physicsState.timeScale = val; }
  get isFastForwarding() { return false; }
  set isFastForwarding(_val: boolean) {}
  get cabinTemperature() { return physicsState.cabinTemperature; }
  get wagonType() { return physicsState.wagonType; }
  get wagonNumber() { return physicsState.wagonNumber; }
  get formattedTime() { return physicsState.formattedTime; }
  get currentKm() { return physicsState.currentKm; }
  get targetSpeed() { return physicsState.targetSpeed; }
  get currentZone() { return physicsState.currentZone; }
  get nextCheckpoint() { return physicsState.nextCheckpoint; }
  get nextStation() { return physicsState.nextStation; }
  get movementStatus() { return physicsState.movementStatus; }
  get progressPercent() { return physicsState.progressPercent; }
  get outdoorTemperature() { return physicsState.outdoorTemperature; }
  get weatherCondition() { return physicsState.weatherCondition; }
  public fastForwardTo(targetTime: string) { this.isEmergencyInterrupted = false; this.emergencyMessage = null; physicsState.jumpToTime(timeStringToSeconds(targetTime)); this.syncAudioPlayback(true); this.syncTripState(); }
  public fastForwardToNextCheckpoint() { const next = this.nextCheckpoint; if (next) this.fastForwardTo(next.checkpoint.plannedTime); }
  public stopFastForward() { physicsState.stopFastForward(); this.isPhaseTransitioning = false; trainAudio.setAmbientDucking(false); }
  public setRealTime() { physicsState.setRealTime(); this.isEmergencyInterrupted = false; this.syncAudioPlayback(true); }
  public jumpTo(cpIndex: number) { const cp = ROUTE_CHECKPOINTS[cpIndex]; if (cp) { this.interrupt(); this.timeSeconds = timeStringToSeconds(cp.plannedTime); this.speed = cp.baseSpeed; this.syncTripState(); } }
  public togglePause() { this.isPaused = !this.isPaused; this.syncAudioPlayback(true); }
  public async startCruisePhase() {
    // Делаем запрос на посадку пассажиров
    try {
      const res = await apiFetch('/api/v1/simulation/trip/board', { method: 'POST' });
      if (res.ok) {
        const manifest = await res.json();
        // Заселяем вагон!
        cabinState.seats = manifest.seats.map((s: any) => convertSeatInfoToPassengerSeat(s));
      }
    } catch (e) {
      console.error('Ошибка при посадке пассажиров', e);
    }

    this.shiftPhase = 'cruise';
    physicsState.isPaused = false;
    
    // Прыгаем ровно на 14:00 (Отправление)
    physicsState.jumpToTime(DEPARTURE_SECONDS); 
    this.timeSeconds = DEPARTURE_SECONDS;
    
    this.showToast('Посадка завершена', 'Пассажиры на местах. Поезд отправляется!');
    this.syncTripState();
  }

  public skipToNextEvent(): void {
    if (this.hasActiveIncident) {
      const incSeat = this.seats.find((s) => s.activeIncident != null);
      this.showToast('Внимание!', `Сначала решите вопрос на месте ${incSeat?.id || ''}!`);
      return;
    }

    // ПЛАВНО ГЛУШИМ СТАРУЮ СТАНЦИЮ ПРИ ПЕРЕМОТКЕ (за 500 мс)
    trainAudio.fadeOutCurrentAnnouncement(500);

    const t = this.timeSeconds;
    const futureEvents = this.activeTimeline
      .filter((e) => !e.triggered && e.timeSec > t)
      .sort((a, b) => a.timeSec - b.timeSec);
    const nextEvent = futureEvents[0];

    let targetTime = ARRIVAL_SECONDS; // По умолчанию - конец маршрута
    const isIncident = nextEvent?.type === 'incident';

    if (!nextEvent) {
      this.timeSkippedText = `Прибытие на конечную станцию...`;
    } else {
      targetTime = nextEvent.timeSec;
      const diffMin = Math.round((targetTime - this.timeSeconds) / 60);

      if (diffMin > 60) {
        const h = Math.floor(diffMin / 60);
        const m = diffMin % 60;
        this.timeSkippedText = `Прошло ${h} ч ${m} мин`;
      } else if (diffMin > 0) {
        this.timeSkippedText = `Прошло ${diffMin} мин`;
      } else {
        this.timeSkippedText = `Прошло несколько секунд...`;
      }
    }

    this.isPhaseTransitioning = true;
    this.isEmergencyInterrupted = false;
    trainAudio.setAmbientDucking(true);

    setTimeout(async () => {
      physicsState.jumpToTime(targetTime);
      this.syncTripState();
    }, 700);

    setTimeout(() => {
      this.isPhaseTransitioning = false;
      trainAudio.setAmbientDucking(false);
      playCallBell();
      if (isIncident) {
        this.showToast('Внимание!', '⚠️ Перемотка прервана: вызов проводника!');
      }
    }, isIncident ? 1400 : 2000);
  }

  // --- ДЕЛЕГАТЫ: CABIN (ВАГОН) ---
  get seats() { return cabinState.seats; }
  get selectedSeatId() { return cabinState.selectedSeatId; }
  set selectedSeatId(val) { cabinState.selectedSeatId = val; }
  get isLoadingManifest() { return cabinState.isLoadingManifest; }
  get isStationEventLoading() { return cabinState.isStationEventLoading; }
  get passengerMood() { return cabinState.passengerMood; }
  set passengerMood(val) { cabinState.passengerMood = val; }
  get currentView() { return cabinState.currentView; }
  set currentView(val) { cabinState.currentView = val; }
  get selectedSeat() { return cabinState.selectedSeat; }
  get currentPassengerSprite() { return cabinState.currentPassengerSprite; }
  get occupiedSeatsCount() { return cabinState.occupiedSeatsCount; }
  get validatedCount() { return cabinState.validatedCount; }
  get alertSeatsCount() { return cabinState.alertSeatsCount; }
  get hasActiveIncident(): boolean { return this.alertSeatsCount > 0; }
  get tverPassengers() { return cabinState.tverPassengers; }
  get tverPassengersCount() { return cabinState.tverPassengersCount; }
  get tverRemindedCount() { return cabinState.tverRemindedCount; }
  get nextStationExitingPassengers() { return cabinState.getNextStationExitingPassengers(this.nextStation?.label || ''); }
  get nextStationRemindedCount() { return this.nextStationExitingPassengers.filter(s => s.isStationExitReminded || s.isTverReminded).length; }

  public switchView(v: CabinView) {
    cabinState.switchView(v);
    trainAudio.setViewMode(v);
  }
  public selectSeat(id: string) { cabinState.selectSeat(id); }
  public setPassengerMood(mood: PassengerMood) { cabinState.setPassengerMood(mood); }
  public inspectSeat(id: string) {
    this.stopFastForward();
    cabinState.inspectSeat(id);
    trainAudio.setViewMode('seat');
  }
  public nextOccupiedSeat() { cabinState.nextOccupiedSeat(); if(this.selectedSeat) this.inspectSeat(this.selectedSeatId); }
  public prevOccupiedSeat() { cabinState.prevOccupiedSeat(); if(this.selectedSeat) this.inspectSeat(this.selectedSeatId); }
  public resetScenario() { cabinState.resetScenario(); }
  public validateCurrentSeat(id?: string) { cabinState.validateCurrentSeat(id); }
  public remindTverPassenger(id?: string) { cabinState.remindTverPassenger(id); }
  public remindStationPassenger(id?: string) { cabinState.remindStationPassenger(id); }
  public loadCabinManifest() { return cabinState.loadCabinManifest(); }
  public resolveIncident(inc: string, opt: string) { return cabinState.resolveIncident(inc, opt); }
  public resolveVoiceIncident(
    inc: string,
    audioBlob: Blob | null,
    text?: string,
    prompt?: string,
    rule?: string
  ) {
    return cabinState.resolveVoiceIncident(inc, audioBlob, text, prompt, rule);
  }
  public fastForwardToTverArrival() { this.fastForwardTo('14:38'); }

  // --- ТОСТЫ УВЕДОМЛЕНИЙ ---
  public showToast(title: string, subtitle: string, durationMs = 3500) {
    if (this.stationToastTimer) clearTimeout(this.stationToastTimer);
    this.stationToast = { title, subtitle };
    if (typeof window !== 'undefined') {
      this.stationToastTimer = setTimeout(() => { this.stationToast = null; this.stationToastTimer = null; }, durationMs);
    }
  }

  // --- ОРКЕСТРАЦИЯ: ИГРОВОЙ ЦИКЛ (TICK) ---
  private startLoop = () => {
    if (typeof window !== 'undefined') {
      const win = window as any;
      if (win.__vsm_raf_id) {
        cancelAnimationFrame(win.__vsm_raf_id);
        win.__vsm_raf_id = null;
      }
      this.lastFrameTime = performance.now();
      const loop = (timestamp: number) => {
        const deltaSec = Math.min((timestamp - this.lastFrameTime) / 1000, 0.1);
        this.lastFrameTime = timestamp;
        this.tick(deltaSec);
        if (typeof window !== 'undefined') {
          this.animationFrameId = requestAnimationFrame(loop);
          win.__vsm_raf_id = this.animationFrameId;
        }
      };
      this.animationFrameId = requestAnimationFrame(loop);
      win.__vsm_raf_id = this.animationFrameId;
    }
  };

  public tick(deltaSec: number): void {
    if (this.isPaused) return;

    physicsState.advanceTimeAndSpeed(deltaSec);
    const t = this.timeSeconds;

    // === ПРОВЕРКА СКРЫТЫХ ЗВУКОВЫХ СОБЫТИЙ (Эмбиент в салоне) ===
    const ambientSeat = this.seats.find((s) => {
      const inc = s.activeIncident;
      if (inc && typeof inc === 'object' && inc.ambient_audio) return true;
      const st = s.passenger?.state || '';
      return st.includes('vaping') || st.includes('crying');
    });

    if (ambientSeat) {
      const inc = typeof ambientSeat.activeIncident === 'object' ? ambientSeat.activeIncident : null;
      const customAudio = inc?.ambient_audio;
      const st = ambientSeat.passenger?.state || '';

      if (customAudio) {
        trainAudio.playEventAmbient(customAudio, 0.25);
      } else if (st.includes('crying')) {
        trainAudio.playEventAmbient('crying_child.mp3', 0.25);
      } else if (st.includes('vaping')) {
        trainAudio.playEventAmbient('vape_hiss.mp3', 0.15);
      } else {
        trainAudio.stopEventAmbient();
      }
    } else {
      trainAudio.stopEventAmbient();
    }

    if (t >= DEPARTURE_SECONDS + 12 && !this.hasPlayedWelcome) {
      this.hasPlayedWelcome = true;
      trainAudio.playVoiceAnnouncement('welcome_msc.wav');
    }

    // Проверяем 10-минутные предупреждения о станциях
    const stations = ROUTE_CHECKPOINTS;
    for (let i = 1; i < stations.length; i++) {
      const st = stations[i];
      const stationSec = timeStringToSeconds(st.plannedTime);

      if (!st.isTechnical && t >= stationSec - 600 && t < stationSec) {
        if (!this.warnedStationIndices.includes(i)) {
          this.warnedStationIndices.push(i);
          const exiting = cabinState.getNextStationExitingPassengers(st.label);
          if (exiting.length > 0) {
            this.shiftPhase = 'station_warning';
            playCallBell();
            this.showToast(
              `🔔 Внимание: ст. ${st.label}`,
              `Прибытие через 10 минут (${st.plannedTime}). На выход: ${exiting.length} пасс. Проверьте готовность!`
            );
          }
        }
      }
    }

    // Проверяем наш таймлайн
    const currentEvents = this.activeTimeline.filter((ev) => t >= ev.timeSec && !ev.triggered);

    for (const ev of currentEvents) {
      ev.triggered = true;

      // Если это инцидент, дергаем бэкенд (или локальный стор)
      if (ev.type === 'incident') {
        this.shiftPhase = 'station_warning';
        
        // Передаем payload (ID инцидента), который прислал бэкенд в таймлайне
        apiFetch('/api/v1/simulation/trip/spawn-specific', { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ incident_id: ev.payload }),
        })
          .then(async (res) => {
            if (res.ok) {
              await this.loadCabinManifest(); // Загружаем обновленный вагон
              const incidentSeat = this.seats.find((s) => s.activeIncident);
              if (incidentSeat) {
                this.reactionTimeLeft = 25; // <--- ПАССАЖИР ЖДЕТ РЕАКЦИИ РОВНО 25 СЕКУНД!
                playCallBell();
                this.showToast('Внимание!', `Вызов проводника на месте ${incidentSeat.id}`);
              }
            }
          });
      }

      // Если это рутинное регламентное событие
      if (ev.type === 'routine') {
        if (typeof ev.payload === 'string') {
          this.showToast('Регламент', ev.payload);
        }
      }

      // Отработка станций (твой старый код из tick() переезжает сюда)
      if (ev.type === 'station_arrival') {
        const stIndex = ev.payload as number;
        const st = ROUTE_CHECKPOINTS[stIndex];
        if (st) {
          this.lastProcessedStationIndex = stIndex;
          if (stIndex === 0) {
            this.showToast('🚀 Отправление', `Поезд отправился со ст. ${st.label}`);
          } else if (st.isTechnical) {
            this.showToast('⚡ Техническая станция', `${st.label} (проезд без остановки)`);
          } else {
            if (stIndex === stations.length - 1 && !this.hasPlayedFinalSpb) {
              this.hasPlayedFinalSpb = true;
              trainAudio.playVoiceAnnouncement('final_spb.wav');
            } else {
              trainAudio.playVoiceAnnouncement(`station_${String(stIndex).padStart(2, '0')}.wav`);
            }
            const unreminded = cabinState
              .getNextStationExitingPassengers(st.label)
              .filter((s) => !s.isStationExitReminded && !s.isTverReminded);
            if (unreminded.length > 0 && stIndex < stations.length - 1) {
              const penalty = unreminded.length * 10;
              conductorState.skills.routine_discipline = Math.max(
                0,
                conductorState.skills.routine_discipline - penalty
              );
              conductorState.emergencyMessage = `Штраф регламента (-${penalty}): ${unreminded.length} пасс. не предупреждены о выходе на ст. ${st.label}!`;
              playErrorSound();
            }
            this.triggerStationEvent(stIndex, st.label);
            this.shiftPhase = stIndex === stations.length - 1 ? 'arrival' : 'cruise';
          }
        }
      }
    }


    // === КОНТРОЛЬ ПОБУДКИ СПЯЩИХ ПАССАЖИРОВ ПЕРЕД СТАНЦИЕЙ ===
    const nextSt = this.nextStation;
    if (nextSt && !nextSt.isTechnical) {
      const stationSec = timeStringToSeconds(nextSt.plannedTime);
      const timeToStation = stationSec - t;

      if (timeToStation > 0 && timeToStation <= 600) {
        for (const s of this.seats) {
          if (
            s.isOccupied &&
            s.passenger &&
            (s.condition === 'sleeping' || s.passenger.state === 'sleeping') &&
            (s.passenger.destination.includes(nextSt.label) || nextSt.label.includes(s.passenger.destination))
          ) {
            // Менее 2 минут до станции (120 сек) и пассажир не разбужен проводником: штраф
            if (timeToStation <= 120 && !s.isStationExitReminded && !s.isSleepingMissedPenaltyApplied) {
              s.isSleepingMissedPenaltyApplied = true;
              const penalty = 15;
              conductorState.skills.routine_discipline = Math.max(
                0,
                conductorState.skills.routine_discipline - penalty
              );
              conductorState.emergencyMessage = `Штраф регламента (-${penalty}): Пассажир на месте ${s.id} не разбужен перед ст. ${nextSt.label}!`;
              playErrorSound();
              this.showToast('Штраф регламента', `Пассажир на месте ${s.id} не разбужен перед ст. ${nextSt.label}!`);
            }
          }
        }
      }
    }

    // === ЛОГИКА ТАЙМЕРА РЕАКЦИИ В ПРОХОДЕ ===
    if (this.currentView === 'aisle' && this.hasActiveIncident && this.reactionTimeLeft > 0) {
      this.reactionTimeLeft -= deltaSec;
      if (this.reactionTimeLeft <= 0) {
        this.reactionTimeLeft = 0;
        const activeSeat = this.seats.find(s => s.activeIncident);
        if (activeSeat && activeSeat.activeIncident) {
          const incId = typeof activeSeat.activeIncident === 'string' 
            ? activeSeat.activeIncident 
            : activeSeat.activeIncident.incident_id;
            
          // Автоматический провал инцидента из-за игнорирования
          this.resolveIncident(incId, 'opt_timeout').then(() => {
            this.showToast('Штраф', `Пассажир на месте ${activeSeat.id} не дождался вас и написал жалобу.`);
            playErrorSound();
          });
        }
      }
    }
  }

  // --- ОРКЕСТРАЦИЯ: СЕРВЕРНАЯ СИНХРОНИЗАЦИЯ ---
  public async fetchTripState() {
    try {
      const res = await apiFetch('/api/v1/simulation/trip/state');
      if (res.ok) {
        const data = await res.json();
        this.timeSeconds = data.time_seconds;
        this.speed = data.speed;
        this.shiftPhase = data.shift_phase;
      }
    } catch {}
  }

  public async syncTripState() {
    try {
      const res = await apiFetch('/api/v1/simulation/trip/state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ time_seconds: this.timeSeconds, speed: this.speed, shift_phase: this.shiftPhase }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.manifest?.seats) {
          cabinState.seats = data.manifest.seats.map(convertSeatInfoToPassengerSeat);
        }
      }
    } catch {}
  }

  public async triggerStationEvent(stationIndex: number, stationName: string): Promise<void> {
    const data = await cabinState.triggerStationEvent(stationIndex);
    if (data && !data.is_technical) {
      this.showToast(`📍 ст. ${data.station_name}`, `Высадка: ${data.disembarked_count} | Посадка: ${data.boarded_count} | В салоне: ${data.total_passengers}/25`);
    }
  }

  public async startNewTrip(mode: string = 'pro'): Promise<void> {
    this.tripMode = mode;
    try {
      const res = await apiFetch('/api/v1/simulation/trip/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      });

      if (res.ok) {
        const data = await res.json();
        
        if (data.manifest?.seats) {
          cabinState.seats = data.manifest.seats.map(convertSeatInfoToPassengerSeat);
        }

        this.activeTimeline = (data.timeline || []).map((ev: any) => ({
          ...ev,
          timeStr: ev.timeStr || secondsToTimeString(ev.timeSec),
          triggered: false,
        }));

        // Синхронизируем физику с бэкендом (Тверь для урока, Москва для PRO)
        physicsState.timeSeconds = data.start_time_seconds || timeStringToSeconds('13:50:00');
        conductorState.shiftPhase = data.start_phase || 'initial_round';
        physicsState.speed = 0; // Поезд стоит на платформе перед стартом
        physicsState.timeScale = 1.0;
        physicsState.isPaused = false;
        
        this.isPhaseTransitioning = false;
        trainAudio.setAmbientDucking(false);
        this.lastProcessedStationIndex = 0;
        this.warnedStationIndices = [];
        this.announcedStationIndices = [];
        this.hasPlayedWelcome = false;
        this.reactionTimeLeft = 0;
        
        // Сбрасываем мини-игры
        this.preTripChecks = { fireExtinguisher: false, climate: false, toilet: false };
        this.postTripItems = [
          { id: 'trash1', type: 'trash', top: '75%', left: '35%', icon: '🥤', isFound: false },
          { id: 'trash2', type: 'trash', top: '82%', left: '60%', icon: '🗞️', isFound: false },
          { id: 'lost1', type: 'lost', top: '65%', left: '25%', icon: '🌂', isFound: false },
        ];
        
        const firstIncidentSeat = cabinState.seats.find((s) => s.activeIncident != null);
        cabinState.selectedSeatId = firstIncidentSeat?.id || '2A';
        cabinState.passengerMood = 'calm';
        cabinState.currentView = 'aisle';
        trainAudio.setViewMode('aisle');
        conductorState.emergencyMessage = null;
        conductorState.isEmergencyInterrupted = false;
        
        this.syncTripState();
        
        const startStation = data.start_phase === 'station_warning' ? 'Тверь' : 'Москва';
        this.showToast('🚀 Рейс начат', `Пункт отправления: ${startStation}. В вагоне: ${cabinState.occupiedSeatsCount}/25 пасс.`);
      }
    } catch (e) {
      console.error('Ошибка старта поездки', e);
    }
  }

  public destroy(): void {
    if (typeof window !== 'undefined') {
      const win = window as any;
      if (this.animationFrameId !== null) {
        cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = null;
      }
      if (win.__vsm_raf_id) {
        cancelAnimationFrame(win.__vsm_raf_id);
        win.__vsm_raf_id = null;
      }
    }
    trainAudio.syncAudioPlayback(false, true);
  }
}

export const trainWorld = new TrainWorldStore();

if (typeof import.meta !== 'undefined' && (import.meta as any).hot) {
  (import.meta as any).hot.dispose(() => {
    trainWorld.destroy();
  });
}
