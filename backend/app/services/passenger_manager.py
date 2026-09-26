import random
from typing import List, Optional
from app.schemas.passenger import CabinManifestResponse, SeatInfo, StationEventResponse
from app.services.passenger_generator import generate_passenger
from app.services.route_stations import ROUTE_STATIONS, TOTAL_STATIONS, StationInfo
from app.services.trip_engine_utils import select_destination, ALL_SEAT_IDS, MAX_PASSENGERS

class PassengerManager:
    """Управляет рассадкой, посадкой и высадкой пассажиров."""

    def __init__(self):
        self.seats: List[SeatInfo] = []

    def generate_initial_manifest(self, min_passengers: int = 13, max_passengers: int = 18) -> None:
        target_count = min(random.randint(min_passengers, max_passengers), MAX_PASSENGERS)
        chosen_seats = random.sample(ALL_SEAT_IDS, target_count)
        occupied_set = set(chosen_seats)

        seats_list: List[SeatInfo] = []
        for seat_id in ALL_SEAT_IDS:
            row = int(seat_id[:-1])
            letter = seat_id[-1]
            if seat_id in occupied_set:
                dest = select_destination(0) # 0 - Москва
                t_status = "validated" if random.random() < 0.6 else "not_checked"
                prof = generate_passenger(destination=dest, ticket_status=t_status, is_boarding=True)
                seats_list.append(SeatInfo(seat_id=seat_id, row=row, letter=letter, is_occupied=True, passenger=prof))
            else:
                seats_list.append(SeatInfo(seat_id=seat_id, row=row, letter=letter, is_occupied=False, passenger=None))
        self.seats = seats_list

    def get_manifest(self) -> CabinManifestResponse:
        occupied = sum(1 for s in self.seats if s.is_occupied)
        validated = sum(1 for s in self.seats if s.is_occupied and s.passenger and s.passenger.ticket_status == "validated")
        return CabinManifestResponse(
            train_number="754",
            wagon_number="03",
            wagon_class="Комфорт",
            total_seats=48,
            occupied_count=occupied,
            validated_count=validated,
            seats=self.seats,
        )

    def process_station(self, station_index: int) -> StationEventResponse:
        st = ROUTE_STATIONS[station_index]
        disembarked, boarded = [], []

        if st.is_technical:
            return self._build_event_response(station_index, st, disembarked, boarded, is_tech=True)

        is_final = station_index == TOTAL_STATIONS - 1

        # Высадка
        for seat in self.seats:
            if seat.is_occupied and seat.passenger:
                if seat.passenger.destination == st.name or is_final:
                    disembarked.append(seat.passenger.full_name)
                    seat.is_occupied = False
                    seat.passenger = None
                    seat.active_incident = None

        # Посадка
        if not is_final:
            current_occupied = sum(1 for s in self.seats if s.is_occupied)
            available_slots = max(0, MAX_PASSENGERS - current_occupied)
            
            raw_incoming = round(random.uniform(1.0, 3.0) * st.weight) if st.name != "Обухово-2" else (1 if random.random() < 0.01 else 0)
            incoming_count = min(available_slots, max(0, raw_incoming))

            free_seats = [s for s in self.seats if not s.is_occupied]
            random.shuffle(free_seats)

            for i in range(min(incoming_count, len(free_seats))):
                seat = free_seats[i]
                dest = select_destination(station_index)
                new_prof = generate_passenger(destination=dest, ticket_status="not_checked")
                seat.is_occupied = True
                seat.passenger = new_prof
                boarded.append(new_prof.full_name)

        return self._build_event_response(station_index, st, disembarked, boarded)

    def _build_event_response(self, idx: int, st: StationInfo, disembarked: list, boarded: list, is_tech: bool = False):
        return StationEventResponse(
            station_index=idx,
            station_name=st.name,
            is_technical=is_tech,
            disembarked_count=len(disembarked),
            disembarked_passengers=disembarked,
            boarded_count=len(boarded),
            boarded_passengers=boarded,
            total_passengers=sum(1 for s in self.seats if s.is_occupied),
            manifest=self.get_manifest(),
        )
