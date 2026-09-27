import unittest
from unittest.mock import patch, AsyncMock
from app.services.polza_service import polza_ai
from app.services.scenarios import get_frontend_incident_data


class TestVoiceExamAndPolza(unittest.IsolatedAsyncioTestCase):
    async def test_polza_mock_fallback(self):
        """Проверка работы Gemini-оценки в безопасном режиме (без ключа или при сбое сети)."""
        res = await polza_ai.evaluate_conductor_voice_response(
            incident_title="Багаж в проходе",
            passenger_prompt="Почему я должен убирать чемодан?",
            conductor_text="Понимаю ваше беспокойство, но проход должен быть свободен ради безопасности. Давайте я помогу переставить его на багажный стеллаж.",
            expected_rule="СТО РЖД 03.011 4-шаговая модель",
        )
        self.assertIn("is_passed", res)
        self.assertTrue(res["is_passed"])
        self.assertIn("loyalty_delta", res)
        self.assertIn("safety_delta", res)
        self.assertIn("feedback_title", res)
        self.assertIn("feedback_text", res)
        self.assertIn("role_model_steps_covered", res)
        self.assertIn("passenger_reply", res)

    def test_frontend_data_preserves_learning_and_voice(self):
        """Проверка передачи phase, expected_rule, why_correct, what_if_wrong на фронт."""
        from app.services.scenarios import SCENARIOS_DB
        SCENARIOS_DB["test_voice_exam"] = {
            "incident_id": "test_voice_exam",
            "title": "Тестовый голосовой экзамен",
            "phase": "voice_exam",
            "start_step": "step_voice",
            "steps": {
                "step_voice": {
                    "action_type": "voice",
                    "expected_rule": "Правило",
                    "prompt": "Вопрос",
                    "options": []
                }
            }
        }
        SCENARIOS_DB["test_learning"] = {
            "incident_id": "test_learning",
            "title": "Тестовое обучение",
            "phase": "learning",
            "start_step": "step_1",
            "steps": {
                "step_1": {
                    "prompt": "Вопрос",
                    "options": [{
                        "id": "opt_1",
                        "text": "Ответ",
                        "why_correct": "Потому что верно",
                        "what_if_wrong": "Опасно"
                    }]
                }
            }
        }

        data_voice = get_frontend_incident_data("test_voice_exam")
        self.assertIsNotNone(data_voice)
        self.assertEqual(data_voice["phase"], "voice_exam")
        self.assertIn("step_voice", data_voice["steps"])
        step = data_voice["steps"]["step_voice"]
        self.assertEqual(step["action_type"], "voice")
        self.assertTrue(len(step["expected_rule"]) > 0)

        data_learning = get_frontend_incident_data("test_learning")
        self.assertIsNotNone(data_learning)
        self.assertEqual(data_learning["phase"], "learning")
        step_1 = data_learning["steps"]["step_1"]
        opt_1 = step_1["options"][0]
        self.assertTrue(len(opt_1.get("why_correct", "")) > 0)
        self.assertTrue(len(opt_1.get("what_if_wrong", "")) > 0)


    async def test_gemini_tts_model_and_voices(self):
        """Проверка отправки параметров Gemini TTS (модель google/gemini-3.8-flash-tts и голоса Puck, Leda, Sulafat)."""
        captured_payloads = []

        class MockResponse:
            status_code = 200
            def json(self):
                return {"audio": "FAKE_BASE64_AUDIO"}

        async def mock_post(url, headers=None, json=None):
            captured_payloads.append(json)
            return MockResponse()

        with patch("httpx.AsyncClient.post", side_effect=mock_post):
            # 1. male_young -> Puck
            res_male = await polza_ai.generate_speech_base64("Тест мужской", archetype="male_young")
            self.assertEqual(res_male, "FAKE_BASE64_AUDIO")
            self.assertEqual(captured_payloads[-1]["model"], "google/gemini-3.8-flash-tts")
            self.assertEqual(captured_payloads[-1]["voice"], "Puck")

            # 2. female_young -> Leda
            res_female = await polza_ai.generate_speech_base64("Тест женский", archetype="female_young")
            self.assertEqual(res_female, "FAKE_BASE64_AUDIO")
            self.assertEqual(captured_payloads[-1]["voice"], "Leda")

            # 3. female_elderly -> Sulafat
            res_elderly = await polza_ai.generate_speech_base64("Тест бабушка", archetype="female_elderly")
            self.assertEqual(res_elderly, "FAKE_BASE64_AUDIO")
            self.assertEqual(captured_payloads[-1]["voice"], "Sulafat")

    async def test_dialog_history_in_voice_prompt(self):
        """Проверка добавления истории реплик в payload LLM."""
        captured_payloads = []

        class MockResponse:
            status_code = 200
            def json(self):
                return {
                    "choices": [{
                        "message": {
                            "content": '{"is_passed": true, "loyalty_delta": 10, "safety_delta": 5, "mood": "happy", "passenger_reply": "Спасибо за чай!", "feedback_title": "Вежливость", "feedback_text": "Хорошо."}'
                        }
                    }]
                }

        async def mock_post(url, headers=None, json=None):
            captured_payloads.append(json)
            return MockResponse()

        history = [
            {"role": "user", "content": "Проводник: «Здравствуйте! Хотите чай или кофе?»"},
            {"role": "assistant", "content": "Пассажир: «Здравствуйте, черный чай, пожалуйста.»"}
        ]

        with patch("httpx.AsyncClient.post", side_effect=mock_post):
            res = await polza_ai.evaluate_conductor_voice_response(
                incident_title="Разговор с пассажиром",
                passenger_prompt="",
                conductor_text="Вот ваш чай с лимоном, приятного аппетита!",
                expected_rule="Вежливое обслуживание",
                dialog_history=history
            )
            self.assertEqual(res["mood"], "happy")
            self.assertEqual(res["passenger_reply"], "Спасибо за чай!")
            sent_messages = captured_payloads[-1]["messages"]
            self.assertEqual(len(sent_messages), 4) # system, 2 history items, user
            self.assertEqual(sent_messages[1]["content"], history[0]["content"])
            self.assertEqual(sent_messages[2]["content"], history[1]["content"])
            self.assertIn("Вот ваш чай", sent_messages[3]["content"])

    def test_seat_free_talk_resolution(self):
        """Проверка разрешения свободного диалога напрямую по seat_id в trip_engine."""
        from app.services.trip_engine import TripEngine
        engine = TripEngine()
        engine.create_new_trip()
        engine.board_passengers(min_passengers=5, max_passengers=10)

        occupied_seat = next((s for s in engine.passenger_manager.seats if s.is_occupied), None)
        self.assertIsNotNone(occupied_seat)
        target_seat_id = occupied_seat.seat_id

        # Разрешаем свободный диалог по номеру кресла
        engine.resolve_incident(target_seat_id, {"mood": "happy", "loyalty_delta": 15})
        self.assertEqual(occupied_seat.passenger.state, "happy")
        self.assertIn("/happy.png", occupied_seat.passenger.sprite_url)
        self.assertEqual(occupied_seat.passenger.ticket_status, "validated")


if __name__ == "__main__":
    unittest.main()
