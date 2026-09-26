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

    def test_frontend_data_preserves_learning_and_voice(self):
        """Проверка передачи phase, expected_rule, why_correct, what_if_wrong на фронт."""
        data_voice = get_frontend_incident_data("inc_voice_exam_01")
        self.assertIsNotNone(data_voice)
        self.assertEqual(data_voice["phase"], "voice_exam")
        self.assertIn("step_voice", data_voice["steps"])
        step = data_voice["steps"]["step_voice"]
        self.assertEqual(step["action_type"], "voice")
        self.assertTrue(len(step["expected_rule"]) > 0)

        data_learning = get_frontend_incident_data("inc_wrong_seat_01")
        self.assertIsNotNone(data_learning)
        self.assertEqual(data_learning["phase"], "learning")
        step_1 = data_learning["steps"]["step_1"]
        opt_1 = step_1["options"][0]
        self.assertTrue(len(opt_1.get("why_correct", "")) > 0)
        self.assertTrue(len(opt_1.get("what_if_wrong", "")) > 0)


if __name__ == "__main__":
    unittest.main()
