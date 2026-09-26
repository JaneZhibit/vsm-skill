import random
from typing import Literal
from app.services.route_stations import ROUTE_STATIONS, TOTAL_STATIONS, StationInfo

MAX_PASSENGERS = 25
ALL_LETTERS: list[Literal["A", "B", "C", "D"]] = ["A", "B", "C", "D"]
ALL_SEAT_IDS = [f"{r}{l}" for r in range(1, 13) for l in ALL_LETTERS]

def get_destination_weight(k: int) -> float:
    if k <= 1: return 1.0
    elif k == 2: return 5.0
    elif k == 3: return 10.0
    elif k == 4: return 20.0
    elif k == 5: return 35.0
    else: return 50.0

def select_destination(from_station_index: int) -> str:
    candidates: list[StationInfo] = []
    weights: list[float] = []

    for idx in range(from_station_index + 1, TOTAL_STATIONS):
        st = ROUTE_STATIONS[idx]
        if st.is_technical: continue
        w = get_destination_weight(idx - from_station_index)
        if st.name == "Обухово-2": w *= 0.1
        candidates.append(st)
        weights.append(w)

    if not candidates: return ROUTE_STATIONS[-1].name
    return random.choices(candidates, weights=weights, k=1)[0].name
