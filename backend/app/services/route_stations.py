"""
Конфигурация эталонного расписания ВСМ-1 «Белый кречет» (Поезд № 754)
Москва (Ленинградский вокзал) — Санкт-Петербург (Главный)
16 станций, 679 км, время в пути 2 ч 15 мин
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StationInfo:
    index: int
    name: str
    km: int
    planned_time: str
    planned_seconds: int
    stop_duration_min: int
    is_technical: bool
    weight: float
    description: str


def time_str_to_seconds(t: str) -> int:
    parts = t.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60


ROUTE_STATIONS: list[StationInfo] = [
    StationInfo(
        index=0,
        name="Москва (Ленинградский вокзал)",
        km=0,
        planned_time="14:00",
        planned_seconds=50400,
        stop_duration_min=0,
        is_technical=False,
        weight=1.0,
        description="Начальная станция. Отправление скоростного экспресса ВСМ-1.",
    ),
    StationInfo(
        index=1,
        name="Рижская",
        km=5,
        planned_time="14:03",
        planned_seconds=50580,
        stop_duration_min=1,
        is_technical=False,
        weight=0.3,
        description="Крупный пересадочный узел в границах Москвы.",
    ),
    StationInfo(
        index=2,
        name="Петровско-Разумовская",
        km=11,
        planned_time="14:06",
        planned_seconds=50760,
        stop_duration_min=1,
        is_technical=False,
        weight=0.4,
        description="Пересадка на МЦД-1, МЦД-3 и метрополитен.",
    ),
    StationInfo(
        index=3,
        name="Зеленоград-Крюково",
        km=41,
        planned_time="14:14",
        planned_seconds=51240,
        stop_duration_min=2,
        is_technical=False,
        weight=1.2,
        description="Крупный транспортный хаб севера Московской агломерации.",
    ),
    StationInfo(
        index=4,
        name="Высоково",
        km=86,
        planned_time="14:24",
        planned_seconds=51840,
        stop_duration_min=1,
        is_technical=False,
        weight=0.4,
        description="Станция в районе г. Клин Московской области.",
    ),
    StationInfo(
        index=5,
        name="Новая Тверь",
        km=167,
        planned_time="14:39",
        planned_seconds=52740,
        stop_duration_min=2,
        is_technical=False,
        weight=2.0,
        description="Ключевой региональный хаб Верхневолжья.",
    ),
    StationInfo(
        index=6,
        name="Логовежь (Торжок)",
        km=225,
        planned_time="14:50",
        planned_seconds=53400,
        stop_duration_min=1,
        is_technical=False,
        weight=0.4,
        description="Раздельный пункт в Торжокском районе Тверской области.",
    ),
    StationInfo(
        index=7,
        name="Садва (Вышний Волочёк)",
        km=280,
        planned_time="15:00",
        planned_seconds=54000,
        stop_duration_min=1,
        is_technical=False,
        weight=0.6,
        description="Станция обслуживания Вышневолоцкого узла.",
    ),
    StationInfo(
        index=8,
        name="Выползово (Бологое)",
        km=330,
        planned_time="15:09",
        planned_seconds=54540,
        stop_duration_min=1,
        is_technical=False,
        weight=0.6,
        description="Исторический железнодорожный узел между двумя столицами.",
    ),
    StationInfo(
        index=9,
        name="Валдай",
        km=398,
        planned_time="15:15",
        planned_seconds=54900,
        stop_duration_min=2,
        is_technical=False,
        weight=1.5,
        description="Крупный хаб Валдайского туристического и рекреационного кластера.",
    ),
    StationInfo(
        index=10,
        name="Горки",
        km=450,
        planned_time="15:24",
        planned_seconds=55440,
        stop_duration_min=0,
        is_technical=True,
        weight=0.0,
        description="Техническая станция. Остановка для посадки/высадки не производится.",
    ),
    StationInfo(
        index=11,
        name="Великий Новгород",
        km=530,
        planned_time="15:41",
        planned_seconds=56460,
        stop_duration_min=2,
        is_technical=False,
        weight=1.8,
        description="Главный вокзал Новгородской области на линии ВСМ.",
    ),
    StationInfo(
        index=12,
        name="Тигода",
        km=590,
        planned_time="15:53",
        planned_seconds=57180,
        stop_duration_min=0,
        is_technical=True,
        weight=0.0,
        description="Техническая станция на границе Новгородской и Ленинградской областей.",
    ),
    StationInfo(
        index=13,
        name="Жаровская",
        km=630,
        planned_time="16:01",
        planned_seconds=57660,
        stop_duration_min=1,
        is_technical=False,
        weight=0.4,
        description="Пассажирская станция Тосненского района Ленинградской области.",
    ),
    StationInfo(
        index=14,
        name="Обухово-2",
        km=668,
        planned_time="16:10",
        planned_seconds=58200,
        stop_duration_min=1,
        is_technical=False,
        weight=0.1,
        description="Южный входной хаб Санкт-Петербургского железнодорожного узла.",
    ),
    StationInfo(
        index=15,
        name="Санкт-Петербург (Главный)",
        km=679,
        planned_time="16:15",
        planned_seconds=58500,
        stop_duration_min=0,
        is_technical=False,
        weight=0.0,
        description="Конечная станция маршрута ВСМ-1. Московский вокзал.",
    ),
]

TOTAL_STATIONS = len(ROUTE_STATIONS)
TOTAL_ROUTE_KM = 679

# Список имен только пассажирских станций
PASSENGER_STATIONS = [s for s in ROUTE_STATIONS if not s.is_technical]
