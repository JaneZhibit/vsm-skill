export type GenderType = 'm' | 'f';
export type ArchetypeId = 'male_young' | 'female_young' | 'female_elderly';
export type TicketStatus = 'validated' | 'not_checked';
export type PassengerCondition = 'calm' | 'annoyed' | 'sleeping' | 'sick' | 'working' | 'drunk';
export type PassengerTrait = 'polite' | 'demanding' | 'anxious';

/**
 * Профиль пассажира с честными паспортными данными РФ,
 * архетипом спрайта и наблюдением проводника
 */
export interface PassengerProfile {
  first_name: string;
  last_name: string;
  patronymic: string;
  full_name: string;
  gender: GenderType;
  trait?: PassengerTrait;
  age: number;
  birth_date: string; // "14.07.2001"
  passport_data: string; // "45 21 849201"
  archetype_id: ArchetypeId;
  state: string; // "neutral", "happy", "annoyed", "sleeping", "gadget", etc.
  sprite_url: string; // "/assets/male_young/neutral.png"
  destination: string;
  ticket_status: TicketStatus;
  observation: string;
}

export interface ScenarioOption {
  id: string;
  text: string;
  action_type?: 'click' | 'hold' | 'voice';
  hold_time_ms?: number;
  next_step?: string;
  why_correct?: string;
  what_if_wrong?: string;
  expected_rule?: string;
  result?: {
    mood?: string;
    loyalty_delta?: number;
    safety_delta?: number;
    feedback?: string;
  };
}

export interface ScenarioStep {
  prompt: string | Record<string, string>;
  timer_seconds: number;
  phase?: 'learning' | 'voice_exam' | 'passive' | 'ambient' | 'urgent' | string;
  action_type?: 'choice' | 'voice' | 'click' | 'hold';
  expected_rule?: string;
  options: ScenarioOption[];
}

export interface ActiveIncident {
  incident_id: string;
  title: string;
  start_step: string;
  phase?: 'learning' | 'voice_exam' | 'passive' | 'ambient' | 'urgent' | string;
  ambient_audio?: string;
  steps: Record<string, ScenarioStep>;
  prompt?: string | Record<string, string>;
  timer_seconds?: number;
  options?: ScenarioOption[];
}

/**
 * Информация о кресле из манифеста вагона
 */
export interface SeatInfo {
  seat_id: string; // "1A", "2B", etc.
  row: number; // 1..12
  letter: 'A' | 'B' | 'C' | 'D';
  is_occupied: boolean;
  passenger?: PassengerProfile | null;
  active_incident?: ActiveIncident | null; // <--- Приходит с бэкенда
}

/**
 * Ответ бэкенда на /api/v1/simulation/cabin-manifest
 */
export interface CabinManifestResponse {
  train_number: string;
  wagon_number: string;
  wagon_class: string;
  total_seats: number;
  occupied_count: number;
  validated_count: number;
  seats: SeatInfo[];
}

/**
 * Ответ бэкенда на /api/v1/simulation/trip/station-event
 */
export interface StationEventResponse {
  station_index: number;
  station_name: string;
  is_technical: boolean;
  disembarked_count: number;
  disembarked_passengers: string[];
  boarded_count: number;
  boarded_passengers: string[];
  total_passengers: number;
  manifest: CabinManifestResponse;
}

/**
 * Расширенная модель места вагона для интерфейсов фронтенда
 */
export interface PassengerSeat extends Omit<SeatInfo, 'active_incident'> {
  id: string; // Алиас для seat_id
  isOccupied: boolean; // Алиас для is_occupied
  passenger?: PassengerProfile;
  passengerName?: string;
  gender?: 'm' | 'f';
  trait?: PassengerTrait;
  destination?: string;
  ticketStatus: TicketStatus;
  condition: PassengerCondition;
  activeIncident?: ActiveIncident | null; // <--- Для удобства на фронте (camelCase)
  notes?: string;
  isTverReminded?: boolean;
  isStationExitReminded?: boolean;
  isSleepingMissedPenaltyApplied?: boolean;
}

export interface CabinConfig {
  wagonNumber: string;
  wagonClass: 'Комфорт' | 'Бизнес' | 'Первый';
  totalRows: number;
  letters: ('A' | 'B' | 'C' | 'D')[];
  occupancyRate: number;
}

/** Глобальная конфигурация вагона класса «Комфорт» */
export const CABIN_CONFIG: CabinConfig = {
  wagonNumber: '03',
  wagonClass: 'Комфорт',
  totalRows: 12,
  letters: ['A', 'B', 'C', 'D'],
  occupancyRate: 0.8,
};

/** Преобразует серверный SeatInfo в PassengerSeat для фронтенда */
export function convertSeatInfoToPassengerSeat(s: SeatInfo): PassengerSeat {
  const p = s.passenger;
  const isOccupied = s.is_occupied;

  let condition: PassengerCondition = 'calm';
  if (p) {
    if (p.state === 'annoyed') condition = 'annoyed';
    else if (p.state === 'sleeping') condition = 'sleeping';
    else if (p.state === 'gadget' || p.state === 'reading') condition = 'working';
    else if (p.state === 'sick') condition = 'sick';
    else if (p.state.startsWith('drunk')) condition = 'drunk';
  }

  return {
    ...s,
    id: s.seat_id,
    isOccupied,
    passenger: p || undefined,
    passengerName: p?.full_name || (isOccupied ? 'Пассажир' : undefined),
    gender: p?.gender,
    trait: p?.trait,
    destination: p?.destination,
    ticketStatus: p?.ticket_status || 'not_checked',
    condition,
    activeIncident: s.active_incident,
    notes: p?.observation,
  };
}
