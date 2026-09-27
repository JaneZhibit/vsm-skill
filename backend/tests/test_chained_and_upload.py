import unittest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.services.game_master import GameMaster
from app.schemas.passenger import SeatInfo, PassengerProfile, ActiveIncidentSchema

class TestChainedAndUpload(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.gm = GameMaster()
        self.gm.init_triggers()

    def test_upload_ambient_audio(self):
        # Valid mp3 file upload
        fake_audio = io.BytesIO(b"FAKE_MP3_DATA")
        response = self.client.post(
            "/api/v1/simulation/upload-ambient-audio",
            files={"file": ("test_custom_bell.mp3", fake_audio, "audio/mpeg")}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["filename"], "test_custom_bell.mp3")

        # Invalid extension
        fake_txt = io.BytesIO(b"NOT_AUDIO")
        bad_response = self.client.post(
            "/api/v1/simulation/upload-ambient-audio",
            files={"file": ("test.txt", fake_txt, "text/plain")}
        )
        self.assertEqual(bad_response.status_code, 400)

    def test_chained_condition_ignored_and_resolved(self):
        # Setup mock passenger seat
        passenger = PassengerProfile(
            first_name="Тест",
            last_name="Пассажиров",
            patronymic="Иванович",
            full_name="Пассажиров Тест Иванович",
            gender="m",
            archetype_id="male_young",
            trait="polite",
            age=25,
            birth_date="01.01.2000",
            passport_data="1234 567890",
            state="annoyed",
            sprite_url="/assets/passengers/male_young/neutral.png",
            destination="Тверь",
            ticket_status="validated",
            observation=""
        )
        seat = SeatInfo(
            seat_id="1A",
            row=1,
            letter="A",
            is_occupied=True,
            passenger=passenger,
            active_incident=ActiveIncidentSchema(
                incident_id="parent_inc_1",
                title="Шумный разговор",
                phase="urgent",
                start_step="step_1",
                steps={}
            )
        )
        seats = [seat]

        # Add chained trigger with condition 'ignored' (fires after 10s if parent is still active)
        self.gm.active_triggers.append({
            "id": "child_ignored",
            "action": "custom_live_event",
            "payload": {
                "incident_id": "child_ignored",
                "title": "Скандал из-за шума",
                "trigger": {"type": "chained", "parent_id": "parent_inc_1", "delay_sec": 10, "condition": "ignored"},
                "allowed_moods": ["angry"],
                "target_archetype": "any"
            }
        })

        # Add chained trigger with condition 'resolved' (fires after 5s after parent is resolved)
        self.gm.active_triggers.append({
            "id": "child_resolved",
            "action": "custom_live_event",
            "payload": {
                "incident_id": "child_resolved",
                "title": "Благодарность соседа",
                "trigger": {"type": "chained", "parent_id": "parent_inc_1", "delay_sec": 5, "condition": "resolved"},
                "allowed_moods": ["happy"],
                "target_archetype": "any"
            }
        })

        # Tick 1: at t=100s, parent_inc_1 is recognized as running
        fired = self.gm.process_tick(current_time=100.0, current_speed=250.0, seats=seats)
        self.assertIn("parent_inc_1", self.gm.running_incidents)
        self.assertEqual(len(fired), 0)

        # Tick 2: at t=105s (< 10s delay), nothing fires yet
        fired = self.gm.process_tick(current_time=105.0, current_speed=250.0, seats=seats)
        self.assertEqual(len(fired), 0)

        # Tick 3: at t=111s (>= 10s delay), 'child_ignored' should fire because parent_inc_1 is still ignored!
        fired = self.gm.process_tick(current_time=111.0, current_speed=250.0, seats=seats)
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0]["id"], "child_ignored")

        # Now simulate parent_inc_1 being resolved (removed from cabin) at t=120s
        seat.active_incident = None
        fired = self.gm.process_tick(current_time=120.0, current_speed=250.0, seats=seats)
        self.assertNotIn("parent_inc_1", self.gm.running_incidents)
        self.assertIn("parent_inc_1", self.gm.resolved_incidents)
        self.assertEqual(self.gm.resolved_incidents["parent_inc_1"], 120.0)

        # Tick 4: at t=122s (< 5s delay after resolution), 'child_resolved' should NOT fire yet
        fired = self.gm.process_tick(current_time=122.0, current_speed=250.0, seats=seats)
        self.assertEqual(len(fired), 0)

        # Tick 5: at t=126s (>= 5s delay after resolution), 'child_resolved' MUST fire!
        fired = self.gm.process_tick(current_time=126.0, current_speed=250.0, seats=seats)
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0]["id"], "child_resolved")

    def test_ambient_audio_propagation(self):
        # Create a live scenario with ambient audio
        payload = {
            "title": "Пассажир с вейпом",
            "target_archetype": "male_young",
            "trigger": {"type": "time", "value": 15},
            "allowed_moods": ["vaping_calm", "vaping_angry"],
            "ambient_audio": "vape_hiss.mp3",
            "is_passive": True,
            "llm_system_prompt": "Пассажир выпускает пар",
            "expected_rule": "Курение запрещено",
            "skills": ["safety"]
        }
        res = self.client.post("/api/v1/simulation/custom-live-scenario", json=payload)
        self.assertEqual(res.status_code, 200)
        inc_id = res.json()["incident_id"]

        from app.services.scenarios import get_frontend_incident_data
        data = get_frontend_incident_data(inc_id)
        self.assertIsNotNone(data)
        self.assertEqual(data.get("ambient_audio"), "vape_hiss.mp3")

        # Test execution on a seat
        passenger = PassengerProfile(
            first_name="Тест",
            last_name="Вейпер",
            patronymic="Тестович",
            full_name="Вейпер Тест Тестович",
            gender="m",
            archetype_id="male_young",
            trait="demanding",
            age=22,
            birth_date="01.01.2002",
            passport_data="1234 567890",
            state="neutral",
            sprite_url="/assets/passengers/male_young/neutral.png",
            destination="Тверь",
            ticket_status="validated",
            observation=""
        )
        seat = SeatInfo(
            seat_id="2A",
            row=2,
            letter="A",
            is_occupied=True,
            passenger=passenger,
            active_incident=None
        )

        from app.api.v1.endpoints.simulation import LIVE_SCENARIOS_DB
        scenario = LIVE_SCENARIOS_DB[inc_id]
        self.gm._execute_live_scenario(scenario, [seat])

        self.assertIsNotNone(seat.active_incident)
        self.assertEqual(seat.active_incident.ambient_audio, "vape_hiss.mp3")
        self.assertIn(seat.passenger.state, ["vaping_calm", "vaping_angry"])

if __name__ == "__main__":
    unittest.main()
