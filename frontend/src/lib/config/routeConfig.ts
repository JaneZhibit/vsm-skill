export type CheckpointType = 'station' | 'bridge' | 'track';

export interface RouteCheckpoint {
  index: number;
  km: number;
  baseSpeed: number; // Базовая целевая скорость в км/ч
  plannedTime: string; // Плановое время в формате "HH:mm"
  label: string; // Название геозоны / объекта
  type: CheckpointType; // Тип участка
  lengthKm?: number; // Длина объекта
  stopDurationMinutes: number; // Длительность стоянки в минутах (0 для проходных и технических)
  isTechnical?: boolean; // Техническая станция без посадки/высадки
  weight?: number; // Вес пассажиропотока
  description: string; // Описание участка
}

export const ROUTE_CHECKPOINTS: RouteCheckpoint[] = [
  {
    index: 0,
    km: 0,
    baseSpeed: 160,
    plannedTime: '14:00',
    label: 'Москва (Ленинградский вокзал)',
    type: 'station',
    stopDurationMinutes: 0,
    weight: 1.0,
    description: 'Начальная станция. Отправление скоростного экспресса ВСМ-1.',
  },
  {
    index: 1,
    km: 5,
    baseSpeed: 0,
    plannedTime: '14:03',
    label: 'Рижская',
    type: 'station',
    stopDurationMinutes: 1,
    weight: 0.3,
    description: 'Крупный пересадочный узел в границах Москвы.',
  },
  {
    index: 2,
    km: 11,
    baseSpeed: 0,
    plannedTime: '14:06',
    label: 'Петровско-Разумовская',
    type: 'station',
    stopDurationMinutes: 1,
    weight: 0.4,
    description: 'Пересадка на МЦД-1, МЦД-3 и метрополитен.',
  },
  {
    index: 3,
    km: 41,
    baseSpeed: 0,
    plannedTime: '14:14',
    label: 'Зеленоград-Крюково',
    type: 'station',
    stopDurationMinutes: 2,
    weight: 1.2,
    description: 'Крупный транспортный хаб севера Московской агломерации.',
  },
  {
    index: 4,
    km: 86,
    baseSpeed: 0,
    plannedTime: '14:24',
    label: 'Высоково',
    type: 'station',
    stopDurationMinutes: 1,
    weight: 0.4,
    description: 'Станция в районе г. Клин Московской области.',
  },
  {
    index: 5,
    km: 167,
    baseSpeed: 0,
    plannedTime: '14:39',
    label: 'Новая Тверь',
    type: 'station',
    stopDurationMinutes: 2,
    weight: 2.0,
    description: 'Ключевой региональный хаб Верхневолжья.',
  },
  {
    index: 6,
    km: 225,
    baseSpeed: 0,
    plannedTime: '14:50',
    label: 'Логовежь (Торжок)',
    type: 'station',
    stopDurationMinutes: 1,
    weight: 0.4,
    description: 'Раздельный пункт в Торжокском районе Тверской области.',
  },
  {
    index: 7,
    km: 280,
    baseSpeed: 0,
    plannedTime: '15:00',
    label: 'Садва (Вышний Волочёк)',
    type: 'station',
    stopDurationMinutes: 1,
    weight: 0.6,
    description: 'Станция обслуживания Вышневолоцкого узла.',
  },
  {
    index: 8,
    km: 330,
    baseSpeed: 0,
    plannedTime: '15:09',
    label: 'Выползово (Бологое)',
    type: 'station',
    stopDurationMinutes: 1,
    weight: 0.6,
    description: 'Исторический железнодорожный узел между двумя столицами.',
  },
  {
    index: 9,
    km: 398,
    baseSpeed: 0,
    plannedTime: '15:15',
    label: 'Валдай',
    type: 'station',
    stopDurationMinutes: 2,
    weight: 1.5,
    description: 'Крупный хаб Валдайского туристического кластера.',
  },
  {
    index: 10,
    km: 450,
    baseSpeed: 380,
    plannedTime: '15:24',
    label: 'Горки',
    type: 'station',
    stopDurationMinutes: 0,
    isTechnical: true,
    weight: 0.0,
    description: 'Техническая станция. Остановка для посадки/высадки не производится.',
  },
  {
    index: 11,
    km: 530,
    baseSpeed: 0,
    plannedTime: '15:41',
    label: 'Великий Новгород',
    type: 'station',
    stopDurationMinutes: 2,
    weight: 1.8,
    description: 'Главный вокзал Новгородской области на линии ВСМ.',
  },
  {
    index: 12,
    km: 590,
    baseSpeed: 380,
    plannedTime: '15:53',
    label: 'Тигода',
    type: 'station',
    stopDurationMinutes: 0,
    isTechnical: true,
    weight: 0.0,
    description: 'Техническая станция на границе Новгородской и Ленинградской областей.',
  },
  {
    index: 13,
    km: 630,
    baseSpeed: 0,
    plannedTime: '16:01',
    label: 'Жаровская',
    type: 'station',
    stopDurationMinutes: 1,
    weight: 0.4,
    description: 'Пассажирская станция Тосненского района Ленинградской области.',
  },
  {
    index: 14,
    km: 668,
    baseSpeed: 0,
    plannedTime: '16:10',
    label: 'Обухово-2',
    type: 'station',
    stopDurationMinutes: 1,
    weight: 0.1,
    description: 'Южный входной хаб Санкт-Петербургского железнодорожного узла.',
  },
  {
    index: 15,
    km: 679,
    baseSpeed: 0,
    plannedTime: '16:15',
    label: 'Санкт-Петербург Главный',
    type: 'station',
    stopDurationMinutes: 0,
    weight: 0.0,
    description: 'Конечная станция маршрута ВСМ-1. Московский вокзал.',
  },
];

export const TOTAL_ROUTE_KM = 679;

/** Преобразование строки времени "HH:mm" или "HH:mm:ss" в секунды от начала суток */
export function timeStringToSeconds(timeStr: string): number {
  const parts = timeStr.split(':').map(Number);
  const hours = parts[0] || 0;
  const minutes = parts[1] || 0;
  const seconds = parts[2] || 0;
  return hours * 3600 + minutes * 60 + seconds;
}

/** Преобразование секунд в формат "HH:mm:ss" */
export function secondsToTimeString(totalSeconds: number, withSeconds = true): string {
  const normalized = Math.max(0, Math.floor(totalSeconds)) % 86400;
  const hours = Math.floor(normalized / 3600);
  const minutes = Math.floor((normalized % 3600) / 60);
  const seconds = normalized % 60;

  const pad = (n: number) => n.toString().padStart(2, '0');
  if (withSeconds) {
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
  }
  return `${pad(hours)}:${pad(minutes)}`;
}

export const DEPARTURE_SECONDS = timeStringToSeconds(ROUTE_CHECKPOINTS[0].plannedTime); // 14:00:00 -> 50400
export const ARRIVAL_SECONDS = timeStringToSeconds(
  ROUTE_CHECKPOINTS[ROUTE_CHECKPOINTS.length - 1].plannedTime
); // 16:15:00 -> 58500
