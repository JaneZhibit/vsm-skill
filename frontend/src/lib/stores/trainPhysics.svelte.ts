import {
  ROUTE_CHECKPOINTS,
  TOTAL_ROUTE_KM,
  timeStringToSeconds,
  secondsToTimeString,
  DEPARTURE_SECONDS,
  ARRIVAL_SECONDS,
  type RouteCheckpoint,
} from '../config/routeConfig';

export type MovementStatus =
  | 'Стоянка (Москва)'
  | 'Разгон'
  | 'Крейсерский ход'
  | 'Торможение'
  | 'Стоянка'
  | 'Прибытие';

function getLegMaxSpeed(legIndex: number): number {
  switch (legIndex) {
    case 0:
      return 120;
    case 1:
      return 160;
    case 2:
      return 200;
    case 3:
      return 280;
    case 4:
      return 360;
    case 14:
      return 160;
    default:
      return 380;
  }
}

export class TrainPhysicsStore {
  timeSeconds = $state<number>(timeStringToSeconds('13:50:00'));
  speed = $state<number>(0);
  isPaused = $state<boolean>(false);
  timeScale = $state<number>(1.0); // Всегда 1.0
  cabinTemperature = $state<number>(24);
  wagonType = $state<'Комфорт'>('Комфорт');
  wagonNumber = $state<string>('03');

  get isFastForwarding(): boolean {
    return false;
  }

  get formattedTime(): string {
    return secondsToTimeString(this.timeSeconds, true);
  }

  get currentKm(): number {
    const t = this.timeSeconds;
    if (t <= DEPARTURE_SECONDS) return 0;
    if (t >= ARRIVAL_SECONDS) return TOTAL_ROUTE_KM;

    for (let i = 0; i < ROUTE_CHECKPOINTS.length - 1; i++) {
      const c1 = ROUTE_CHECKPOINTS[i];
      const c2 = ROUTE_CHECKPOINTS[i + 1];
      const t1 = timeStringToSeconds(c1.plannedTime);
      const t2 = timeStringToSeconds(c2.plannedTime);
      const departTime1 = t1 + (c1.stopDurationMinutes || 0) * 60;

      if (t >= t1 && t < departTime1) return c1.km;
      if (t >= departTime1 && t <= t2) {
        const spanTime = Math.max(1, t2 - departTime1);
        const progress = Math.min(1, Math.max(0, (t - departTime1) / spanTime));
        return Math.round((c1.km + (c2.km - c1.km) * progress) * 10) / 10;
      }
    }
    return TOTAL_ROUTE_KM;
  }

  get targetSpeed(): number {
    const t = this.timeSeconds;
    if (t < DEPARTURE_SECONDS || t >= ARRIVAL_SECONDS) return 0;

    for (let i = 0; i < ROUTE_CHECKPOINTS.length - 1; i++) {
      const c1 = ROUTE_CHECKPOINTS[i];
      const c2 = ROUTE_CHECKPOINTS[i + 1];
      const t1 = timeStringToSeconds(c1.plannedTime);
      const t2 = timeStringToSeconds(c2.plannedTime);
      const departTime1 = t1 + (c1.stopDurationMinutes || 0) * 60;

      if (t >= t1 && t < departTime1) return 0;
      if (t >= departTime1 && t <= t2) {
        const span = Math.max(1, t2 - departTime1);
        const progress = Math.min(1, Math.max(0, (t - departTime1) / span));
        const legSpeed = getLegMaxSpeed(i);
        const willStopAtC2 =
          !c2.isTechnical && (c2.stopDurationMinutes > 0 || i === ROUTE_CHECKPOINTS.length - 2);

        if (willStopAtC2 && progress > 0.75) {
          return Math.max(0, Math.round(legSpeed * (1 - (progress - 0.75) / 0.25)));
        }
        if (c1.stopDurationMinutes > 0 || i === 0) {
          if (progress < 0.25) return Math.max(20, Math.round(legSpeed * (progress / 0.25)));
        }
        return legSpeed;
      }
    }
    return 0;
  }

  get currentZone(): RouteCheckpoint {
    const t = this.timeSeconds;
    if (t <= DEPARTURE_SECONDS) return ROUTE_CHECKPOINTS[0];
    if (t >= ARRIVAL_SECONDS) return ROUTE_CHECKPOINTS[ROUTE_CHECKPOINTS.length - 1];

    for (let i = 0; i < ROUTE_CHECKPOINTS.length - 1; i++) {
      const c1 = ROUTE_CHECKPOINTS[i];
      const c2 = ROUTE_CHECKPOINTS[i + 1];
      const t1 = timeStringToSeconds(c1.plannedTime);
      const t2 = timeStringToSeconds(c2.plannedTime);
      const departTime1 = t1 + (c1.stopDurationMinutes || 0) * 60;

      if (t >= t1 && t < departTime1) return c1;
      if (t >= departTime1 && t <= t2) {
        const midTime = departTime1 + (t2 - departTime1) / 2;
        return t < midTime ? c1 : c2;
      }
    }
    return ROUTE_CHECKPOINTS[ROUTE_CHECKPOINTS.length - 1];
  }

  get nextCheckpoint() {
    const t = this.timeSeconds;
    const currentKm = this.currentKm;
    for (const cp of ROUTE_CHECKPOINTS) {
      const cpTime = timeStringToSeconds(cp.plannedTime);
      if (cpTime > t && cp.km > currentKm) {
        return {
          checkpoint: cp,
          distanceKm: Math.max(0, Math.round((cp.km - currentKm) * 10) / 10),
          etaMinutes: Math.round((cpTime - t) / 60),
        };
      }
    }
    return null;
  }

  get nextStation(): RouteCheckpoint | null {
    const t = this.timeSeconds;
    for (let i = 1; i < ROUTE_CHECKPOINTS.length; i++) {
      const cp = ROUTE_CHECKPOINTS[i];
      if (timeStringToSeconds(cp.plannedTime) > t && !cp.isTechnical) {
        return cp;
      }
    }
    return null;
  }

  get movementStatus(): MovementStatus {
    const t = this.timeSeconds;
    const speed = Math.round(this.speed);
    const target = this.targetSpeed;
    if (t < DEPARTURE_SECONDS) return 'Стоянка (Москва)';
    if (t >= ARRIVAL_SECONDS || this.currentKm >= TOTAL_ROUTE_KM - 0.5) return 'Прибытие';
    if (speed < 3 && target === 0) return 'Стоянка';
    if (speed < target - 10) return 'Разгон';
    if (speed > target + 10) return 'Торможение';
    return 'Крейсерский ход';
  }

  get progressPercent(): number {
    return Math.min(100, Math.max(0, Math.round((this.currentKm / TOTAL_ROUTE_KM) * 1000) / 10));
  }

  get outdoorTemperature(): number {
    return Math.round(21 - (this.progressPercent / 100) * 3);
  }

  get weatherCondition(): string {
    return this.progressPercent > 55 ? 'Переменная облачность' : 'Ясно';
  }

  public advanceTimeAndSpeed(deltaSec: number = 1.0): void {
    if (this.isPaused) return;

    // Идем строго 1 к 1
    this.timeSeconds += deltaSec * this.timeScale;

    if (this.timeSeconds > ARRIVAL_SECONDS) {
      this.timeSeconds = ARRIVAL_SECONDS;
    }

    // Корректируем скорость под целевую
    if (this.speed < this.targetSpeed) {
      this.speed = Math.min(this.targetSpeed, this.speed + 1.2 * deltaSec);
    } else if (this.speed > this.targetSpeed) {
      this.speed = Math.max(this.targetSpeed, this.speed - 2.0 * deltaSec);
    }
  }

  // Вместо fastForwardTo делаем мгновенный прыжок
  public jumpToTime(targetSec: number): void {
    this.timeSeconds = targetSec;
    this.speed = this.targetSpeed; // при прыжке сразу выходим на рабочую скорость
  }

  public fastForwardTo(targetTimeStr: string): void {
    this.jumpToTime(timeStringToSeconds(targetTimeStr));
  }

  public stopFastForward(): void {
    // Больше не используется, оставили для совместимости
  }

  public setRealTime(): void {
    this.isPaused = false;
  }
}

export const physicsState = new TrainPhysicsStore();
