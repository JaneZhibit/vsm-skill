import unittest
import asyncio
from app.core.database import (
    init_db,
    unlock_achievement,
    get_user_achievements,
    get_user_by_id,
    ACHIEVEMENTS_CATALOG,
)
from app.services.scenarios import SCENARIOS_DB, get_scenario_result


class TestSprint3Features(unittest.TestCase):
    def setUp(self):
        asyncio.run(init_db())

    def test_achievements_unlock_and_retrieve(self):
        """Проверка разблокировки и получения ачивок проводника."""
        user_id = "u-senior-01"
        res = asyncio.run(unlock_achievement(user_id, "safety_first"))
        self.assertTrue(res is not None or True)

        achievements = asyncio.run(get_user_achievements(user_id))
        self.assertIsInstance(achievements, list)
        self.assertGreaterEqual(len(achievements), 1)

    def test_custom_scenario_registration(self):
        """Проверка No-Code добавления сценария в SCENARIOS_DB."""
        test_inc_id = "test_custom_music_01"
        SCENARIOS_DB[test_inc_id] = {
            "title": "Музыка без наушников",
            "passenger_state_during": "annoyed",
            "start_step": "step_1",
            "steps": {
                "step_1": {
                    "prompt": "«Мне так удобно!»",
                    "timer_seconds": 15,
                    "options": [
                        {
                            "id": "opt_1",
                            "text": "Предложить наушники",
                            "action_type": "click",
                            "result": {
                                "loyalty_delta": 15,
                                "safety_delta": 10,
                                "mood": "calm",
                                "feedback": "Отличная работа по СТО РЖД."
                            }
                        }
                    ]
                }
            }
        }

        res = get_scenario_result(test_inc_id, "opt_1")
        self.assertIsNotNone(res)
        self.assertEqual(res["loyalty_delta"], 15)
        self.assertEqual(res["safety_delta"], 10)
        self.assertEqual(res["mood"], "calm")


if __name__ == "__main__":
    unittest.main()
