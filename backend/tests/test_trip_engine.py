"""
Юнит-тесты движка поездки ВСМ-1 (TripEngine) и математической модели пассажиропотока.
"""

import unittest
from app.services.trip_engine import TripEngine, MAX_PASSENGERS
from app.services.route_stations import ROUTE_STATIONS, TOTAL_STATIONS
from app.services.scenarios import SCENARIOS_DB


class TestTripEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TripEngine()

    def test_new_trip_generation(self):
        """Проверка инициализации рейса: пустой вагон при приемке, затем 13-18 пассажиров при посадке."""
        for _ in range(10):
            trip_data = self.engine.create_new_trip(min_passengers=13, max_passengers=18)
            manifest = trip_data["manifest"]
            self.assertEqual(manifest.total_seats, 48)
            # В фазе приемки (13:50) вагон пуст
            self.assertEqual(manifest.occupied_count, 0)

            # Посадка пассажиров перед отправлением (14:00)
            boarded_manifest = self.engine.board_passengers(min_passengers=13, max_passengers=18)
            self.assertGreaterEqual(boarded_manifest.occupied_count, 13)
            self.assertLessEqual(boarded_manifest.occupied_count, 18)
            self.assertLessEqual(boarded_manifest.occupied_count, MAX_PASSENGERS)

            # Проверка занятых мест
            occupied_seats = [s for s in boarded_manifest.seats if s.is_occupied]
            for s in occupied_seats:
                self.assertIsNotNone(s.passenger)
                self.assertTrue(len(s.passenger.full_name) > 0)

            # Проверка отсутствия технических станций в качестве назначения
            for s in boarded_manifest.seats:
                if s.is_occupied and s.passenger:
                    self.assertNotIn(s.passenger.destination, ["Горки", "Тигода"])

    def test_full_route_simulation(self):
        """Симуляция прохождения всех 16 станций маршрута от Москвы до СПб."""
        self.engine.create_new_trip(min_passengers=15, max_passengers=15)
        self.engine.board_passengers(min_passengers=15, max_passengers=15)

        for idx in range(1, TOTAL_STATIONS):
            st = ROUTE_STATIONS[idx]
            event = self.engine.process_station_arrival(idx)

            # Проверка технических станций
            if st.is_technical:
                self.assertTrue(event.is_technical)
                self.assertEqual(event.disembarked_count, 0)
                self.assertEqual(event.boarded_count, 0)
            else:
                self.assertFalse(event.is_technical)

            # Вагон никогда не должен превышать MAX_PASSENGERS
            self.assertLessEqual(event.total_passengers, MAX_PASSENGERS)

            # На конечной станции в Санкт-Петербурге все пассажиры должны выйти
            if idx == TOTAL_STATIONS - 1:
                self.assertEqual(event.total_passengers, 0)

    def test_passenger_traits(self):
        """Проверка генерации черт характера (traits) и пола."""
        self.engine.create_new_trip(min_passengers=15, max_passengers=15)
        manifest = self.engine.board_passengers(min_passengers=15, max_passengers=15)
        for s in manifest.seats:
            if s.is_occupied and s.passenger:
                self.assertIn(s.passenger.trait, ["polite", "anxious", "demanding"])
                self.assertIn(s.passenger.gender, ["m", "f"])

    def test_multi_step_scenario(self):
        """Проверка структуры и резолва инцидентов СТО РЖД с двойной шкалой."""
        from app.services.scenarios import get_scenario_result, get_frontend_incident_data
        data = get_frontend_incident_data("inc_ebs_01")
        self.assertIsNotNone(data)
        self.assertEqual(data["start_step"], "step_1")
        self.assertIn("steps", data)
        self.assertIn("step_1", data["steps"])

        # Проверка резолва опции с safety_delta
        res = get_scenario_result("inc_ebs_01", "opt_1")
        self.assertIsNotNone(res)
        self.assertEqual(res["mood"], "calm")
        self.assertEqual(res["loyalty_delta"], 20)
        self.assertEqual(res["safety_delta"], 20)

    def test_generate_timeline(self):
        """Проверка генерации таймлайна (4 инцидента по маршруту)."""
        tl = self.engine.generate_timeline(mode="level_1")
        self.assertTrue(len(tl) > 0)
        incidents = [ev for ev in tl if ev["type"] == "incident"]
        self.assertEqual(len(incidents), 4)
        for inc in incidents:
            self.assertIn(inc["payload"], SCENARIOS_DB)

        # Проверка сортировки по timeSec
        time_secs = [ev["timeSec"] for ev in tl]
        self.assertEqual(time_secs, sorted(time_secs))


if __name__ == "__main__":
    unittest.main()
