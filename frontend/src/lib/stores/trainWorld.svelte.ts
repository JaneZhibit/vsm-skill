// frontend/src/lib/stores/trainWorld.svelte.ts
import { apiFetch } from '../services/api';
import {
  ROUTE_CHECKPOINTS,
  timeStringToSeconds,
  secondsToTimeString,
  DEPARTURE_SECONDS,
  ARRIVAL_SECONDS,
} from '../config/routeConfig';
import { playCallBell, playErrorSound } from '../utils/audio';

import { trainAudio } from './trainAudio.svelte';
import { conductorState } from './conductorState.svelte';
import { physicsState } from './trainPhysics.svelte';
import { cabinState } from './cabinState.svelte';
import { convertSeatInfoToPassengerSeat } from '../config/cabinConfig';
import { gameLoop } from '../services/gameLoop.svelte';

export type TimelineEventType = 'station_arrival' | 'incident' | 'routine';

export interface TimelineEvent {
  id: string;
  timeStr: string;
  timeSec: number;
  type: TimelineEventType;
  payload?: any;
  triggered: boolean;
}

export class TrainWorldStore {
  tripMode = $state<string>('pro');
  isPhaseTransitioning = $state<boolean>(false);
  timeSkippedText = $state<string>('');
  activeTimeline = $state<TimelineEvent[]>([]);
  reactionTimeLeft = $state<number>(0);

  preTripChecks = $state({ fireExtinguisher: false, climate: false, toilet: false });
  cleaningProgress = $state<number>(0);

  get isPreTripDone() {
    return this.preTripChecks.fireExtinguisher && this.preTripChecks.climate && this.preTripChecks.toilet;
  }

  get isPostTripDone() {
    return this.cleaningProgress >= 70;
  }

  lastProcessedStationIndex = $state<number>(0);
  warnedStationIndices = $state<number[]>([]);
  announcedStationIndices = $state<number[]>([]);
  hasPlayedWelcome = $state<boolean>(false);
  hasPlayedFinalSpb = $state<boolean>(false);
  
  stationToast = $state<{ title: string; subtitle: string } | null>(null);
  private stationToastTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      cabinState.loadCabinManifest().then(() => {
        this.fetchTripState();
      });
      gameLoop.start(); // Запускаем цикл из отдельного сервиса
      setInterval(() => { if (!physicsState.isPaused) this.syncTripState(); }, 5000);
    }
  }

  public abortTrip(): void {
    this.activeTimeline = [];
    physicsState.isPaused = true;
    trainAudio.stopAmbient(true);
  }

  public showToast(title: string, subtitle: string, durationMs = 3500) {
    if (this.stationToastTimer) clearTimeout(this.stationToastTimer);
    this.stationToast = { title, subtitle };
    if (typeof window !== 'undefined') {
      this.stationToastTimer = setTimeout(() => { this.stationToast = null; this.stationToastTimer = null; }, durationMs);
    }
  }

  public async startCruisePhase() {
    this.isPhaseTransitioning = true;
    this.timeSkippedText = 'Пассажиры занимают свои места...';

    apiFetch('/api/v1/simulation/trip/board', { method: 'POST' }).then(async (res) => {
      if (res.ok) {
        const manifest = await res.json();
        cabinState.seats = manifest.seats.map((s: any) => convertSeatInfoToPassengerSeat(s));
      }
    }).catch(e => console.error('Ошибка при посадке пассажиров', e));

    setTimeout(() => {
      conductorState.shiftPhase = 'cruise';
      physicsState.isPaused = false;
      physicsState.jumpToTime(DEPARTURE_SECONDS); 
      this.showToast('Посадка завершена', 'Пассажиры на местах. Поезд отправляется!');
      this.isPhaseTransitioning = false;
      this.syncTripState();
    }, 2500);
  }

  public skipToNextEvent(): void {
    if (cabinState.alertSeatsCount > 0) {
      const incSeat = cabinState.seats.find((s) => s.activeIncident != null);
      this.showToast('Внимание!', `Сначала решите вопрос на месте ${incSeat?.id || ''}!`);
      return;
    }

    trainAudio.fadeOutCurrentAnnouncement(500);
    const t = physicsState.timeSeconds;
    const futureEvents = this.activeTimeline
      .filter((e) => !e.triggered && e.timeSec > t)
      .sort((a, b) => a.timeSec - b.timeSec);
    const nextEvent = futureEvents[0];

    let targetTime = ARRIVAL_SECONDS;
    const isIncident = nextEvent?.type === 'incident';

    if (!nextEvent) {
      this.timeSkippedText = `Прибытие на конечную станцию...`;
    } else {
      targetTime = nextEvent.timeSec;
      const diffMin = Math.round((targetTime - t) / 60);

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
    conductorState.isEmergencyInterrupted = false;
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

  public tick(deltaSec: number): void {
    if (physicsState.isPaused) return;

    physicsState.advanceTimeAndSpeed(deltaSec);
    const t = physicsState.timeSeconds;

    const ambientSeat = cabinState.seats.find((s) => {
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

    if (t >= DEPARTURE_SECONDS + 1 && !this.hasPlayedWelcome) {
      this.hasPlayedWelcome = true;
      trainAudio.playVoiceAnnouncement('welcome_msc.wav');
    }

    const stations = ROUTE_CHECKPOINTS;
    for (let i = 1; i < stations.length; i++) {
      const st = stations[i];
      const stationSec = timeStringToSeconds(st.plannedTime);

      if (!st.isTechnical && t >= stationSec - 600 && t < stationSec) {
        if (!this.warnedStationIndices.includes(i)) {
          this.warnedStationIndices.push(i);
          const exiting = cabinState.getNextStationExitingPassengers(st.label);
          if (exiting.length > 0) {
            conductorState.shiftPhase = 'station_warning';
            playCallBell();
            this.showToast(
              `🔔 Внимание: ст. ${st.label}`,
              `Прибытие через 10 минут (${st.plannedTime}). На выход: ${exiting.length} пасс. Проверьте готовность!`
            );
          }
        }
      }
    }

    const currentEvents = this.activeTimeline.filter((ev) => t >= ev.timeSec && !ev.triggered);

    for (const ev of currentEvents) {
      ev.triggered = true;

      if (ev.type === 'incident') {
        conductorState.shiftPhase = 'station_warning';
        apiFetch('/api/v1/simulation/trip/spawn-specific', { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ incident_id: ev.payload }),
        }).then(async (res) => {
            if (res.ok) {
              await cabinState.loadCabinManifest();
              const incidentSeat = cabinState.seats.find((s) => s.activeIncident);
              if (incidentSeat) {
                this.reactionTimeLeft = 25;
                playCallBell();
                this.showToast('Внимание!', `Вызов проводника на месте ${incidentSeat.id}`);
              }
            }
          });
      }

      if (ev.type === 'routine') {
        if (typeof ev.payload === 'string') {
          this.showToast('Регламент', ev.payload);
        }
      }

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
            const unreminded = cabinState.getNextStationExitingPassengers(st.label).filter((s) => !s.isStationExitReminded && !s.isTverReminded);
            if (unreminded.length > 0 && stIndex < stations.length - 1) {
              const penalty = unreminded.length * 10;
              conductorState.skills.routine_discipline = Math.max(0, conductorState.skills.routine_discipline - penalty);
              conductorState.emergencyMessage = `Штраф регламента (-${penalty}): ${unreminded.length} пасс. не предупреждены о выходе на ст. ${st.label}!`;
              playErrorSound();
            }
            this.triggerStationEvent(stIndex, st.label);
            conductorState.shiftPhase = stIndex === stations.length - 1 ? 'arrival' : 'cruise';
          }
        }
      }
    }

    const nextSt = physicsState.nextStation;
    if (nextSt && !nextSt.isTechnical) {
      const stationSec = timeStringToSeconds(nextSt.plannedTime);
      const timeToStation = stationSec - t;

      if (timeToStation > 0 && timeToStation <= 600) {
        for (const s of cabinState.seats) {
          if (
            s.isOccupied && s.passenger &&
            (s.condition === 'sleeping' || s.passenger.state === 'sleeping') &&
            (s.passenger.destination.includes(nextSt.label) || nextSt.label.includes(s.passenger.destination))
          ) {
            if (timeToStation <= 120 && !s.isStationExitReminded && !s.isSleepingMissedPenaltyApplied) {
              s.isSleepingMissedPenaltyApplied = true;
              const penalty = 15;
              conductorState.skills.routine_discipline = Math.max(0, conductorState.skills.routine_discipline - penalty);
              conductorState.emergencyMessage = `Штраф регламента (-${penalty}): Пассажир на месте ${s.id} не разбужен перед ст. ${nextSt.label}!`;
              playErrorSound();
              this.showToast('Штраф регламента', `Пассажир на месте ${s.id} не разбужен перед ст. ${nextSt.label}!`);
            }
          }
        }
      }
    }

    if (cabinState.currentView === 'aisle' && cabinState.alertSeatsCount > 0 && this.reactionTimeLeft > 0) {
      this.reactionTimeLeft -= deltaSec;
      if (this.reactionTimeLeft <= 0) {
        this.reactionTimeLeft = 0;
        const activeSeat = cabinState.seats.find(s => s.activeIncident);
        if (activeSeat && activeSeat.activeIncident) {
          const incId = typeof activeSeat.activeIncident === 'string' ? activeSeat.activeIncident : activeSeat.activeIncident.incident_id;
          cabinState.resolveIncident(incId, 'opt_timeout').then(() => {
            this.showToast('Штраф', `Пассажир на месте ${activeSeat.id} не дождался вас и написал жалобу.`);
            playErrorSound();
          });
        }
      }
    }
  }

  public async fetchTripState() {
    try {
      const res = await apiFetch('/api/v1/simulation/trip/state');
      if (res.ok) {
        const data = await res.json();
        physicsState.timeSeconds = data.time_seconds;
        physicsState.speed = data.speed;
        conductorState.shiftPhase = data.shift_phase;
      }
    } catch {}
  }

  public async syncTripState() {
    try {
      const res = await apiFetch('/api/v1/simulation/trip/state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ time_seconds: physicsState.timeSeconds, speed: physicsState.speed, shift_phase: conductorState.shiftPhase }),
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
      this.showToast(`📍 ст. ${data.station_name}`, `Высадка: ${data.disembarked_count} | Посадка: ${data.boarded_count} | В салоне: ${data.total_passengers}/48`);
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
        if (data.manifest?.seats) cabinState.seats = data.manifest.seats.map(convertSeatInfoToPassengerSeat);

        this.activeTimeline = (data.timeline || []).map((ev: any) => ({
          ...ev,
          timeStr: ev.timeStr || secondsToTimeString(ev.timeSec),
          triggered: false,
        }));

        physicsState.timeSeconds = data.start_time_seconds || timeStringToSeconds('13:50:00');
        conductorState.shiftPhase = data.start_phase || 'initial_round';
        physicsState.speed = 0;
        physicsState.timeScale = 1.0;
        physicsState.isPaused = false;
        
        this.isPhaseTransitioning = false;
        trainAudio.setAmbientDucking(false);
        this.lastProcessedStationIndex = 0;
        this.warnedStationIndices = [];
        this.announcedStationIndices = [];
        this.hasPlayedWelcome = false;
        this.reactionTimeLeft = 0;
        
        this.preTripChecks = { fireExtinguisher: false, climate: false, toilet: false };
        this.cleaningProgress = 0;
        
        const firstIncidentSeat = cabinState.seats.find((s) => s.activeIncident != null);
        cabinState.selectedSeatId = firstIncidentSeat?.id || '2A';
        cabinState.passengerMood = 'calm';
        cabinState.currentView = 'aisle';
        trainAudio.setViewMode('aisle');
        conductorState.emergencyMessage = null;
        conductorState.isEmergencyInterrupted = false;
        
        this.syncTripState();
        
        const startStation = data.start_phase === 'station_warning' ? 'Тверь' : 'Москва';
        this.showToast('🚀 Рейс начат', `Пункт отправления: ${startStation}. В вагоне: ${cabinState.occupiedSeatsCount}/48 пасс.`);
      }
    } catch (e) {
      console.error('Ошибка старта поездки', e);
    }
  }

  public destroy(): void {
    gameLoop.stop();
    trainAudio.syncAudioPlayback(false, true);
  }
}

export const trainWorld = new TrainWorldStore();

if (typeof import.meta !== 'undefined' && (import.meta as any).hot) {
  (import.meta as any).hot.dispose(() => {
    trainWorld.destroy();
  });
}