export type ShiftPhase = 'initial_round' | 'cruise' | 'station_warning' | 'tver_warning' | 'arrival';

export interface ConductorProfile {
  name: string;
  gender: 'm' | 'f';
  role: string;
  badge: string;
  shiftsCompleted: number;
  incidentsResolved: number;
  correctDecisions: number;
  accuracyPercent: number;
  streakDays: number;
  ratingScore: number;
}

export interface ConductorSkills {
  service_psychology: number;
  safety_tech: number;
  routine_discipline: number;
  first_aid: number;
}

export interface UnlockedAchievement {
  code: string;
  title: string;
  description: string;
  icon: string;
}

export class ConductorStateStore {
  conductorProfile = $state<ConductorProfile>({
    name: 'Алексей Смирнов',
    gender: 'm',
    role: 'Старший проводник',
    badge: 'ВСМ-1 • Бизнес-класс',
    shiftsCompleted: 14,
    incidentsResolved: 22,
    correctDecisions: 18,
    accuracyPercent: 82,
    streakDays: 4,
    ratingScore: 310,
  });

  skills = $state<ConductorSkills>({
    service_psychology: 85,
    safety_tech: 100,
    routine_discipline: 65,
    first_aid: 40,
  });

  loyaltyScore = $state<number>(85);
  safetyScore = $state<number>(100);
  shiftPhase = $state<ShiftPhase>('initial_round');
  isEmergencyInterrupted = $state<boolean>(false);
  emergencyMessage = $state<string | null>(null);

  // Плашка нового достижения
  achievementToast = $state<UnlockedAchievement | null>(null);
  private achTimer: ReturnType<typeof setTimeout> | null = null;

  public showAchievementBanner(ach: UnlockedAchievement): void {
    if (this.achTimer) clearTimeout(this.achTimer);
    this.achievementToast = ach;
    this.achTimer = setTimeout(() => {
      this.achievementToast = null;
      this.achTimer = null;
    }, 5000);
  }

  get overallReadiness(): number {
    const { service_psychology, safety_tech, routine_discipline, first_aid } = this.skills;
    return Math.round((service_psychology + safety_tech + routine_discipline + first_aid) / 4);
  }

  get weakestSkill() {
    const items = [
      {
        key: 'first_aid',
        name: 'Доврачебная помощь',
        score: this.skills.first_aid,
        recommendation:
          'В режиме ПРО система повысит шанс генерации медицинских кейсов (кинетоз, аптечка, поиск врача в вагоне).',
      },
      {
        key: 'routine_discipline',
        name: 'Дисциплина и регламент',
        score: this.skills.routine_discipline,
        recommendation:
          'В режиме ПРО система сфокусируется на контроле посадки, рассадке и соблюдении норм СТО РЖД.',
      },
      {
        key: 'service_psychology',
        name: 'Сервис и психология',
        score: this.skills.service_psychology,
        recommendation:
          'В режиме ПРО система подберет сложных и конфликтных пассажиров для тренировки деэскалации.',
      },
      {
        key: 'safety_tech',
        name: 'Техногенная безопасность',
        score: this.skills.safety_tech,
        recommendation:
          'В режиме ПРО будут проверяться антитеррор, датчики дыма и электробезопасность на 400 км/ч.',
      },
    ];
    items.sort((a, b) => a.score - b.score);
    return items[0];
  }

  public triggerEmergency(reason: string): void {
    this.isEmergencyInterrupted = true;
    this.emergencyMessage = reason;
    setTimeout(() => {
      if (this.isEmergencyInterrupted) {
        this.isEmergencyInterrupted = false;
      }
    }, 4000);
  }
}

export const conductorState = new ConductorStateStore();
