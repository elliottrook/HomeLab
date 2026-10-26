import unittest
from pathlib import Path

import fixed_doctor_deterministic_answer as deterministic
import fixed_doctor_usefulness as usefulness


FIXTURE = Path(__file__).with_name("fixtures") / "fixed-doctor-usefulness-v1.json"


class FixedDoctorDeterministicAnswerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = usefulness.load_unique(FIXTURE.read_bytes())
        usefulness.validate(cls.fixture)

    def test_all_cases_report_state_freshness_scope_and_limit(self):
        for case in self.fixture["cases"]:
            with self.subTest(case=case["id"]):
                value = deterministic.answer(case)
                observation = case["observation"]
                self.assertIn(observation["observed_at"], value)
                self.assertIn(f"{observation['age_seconds']} seconds old", value)
                self.assertIn("cannot establish a cause or a repair", value)
                self.assertIn("does not establish broader system health", value)
                if observation["state"] == "unavailable":
                    self.assertIn("is unavailable", value)
                    self.assertIn("No inference-health fact", value)
                else:
                    self.assertIn(
                        f"reports {deterministic.STATES[observation['state']]}", value,
                    )
                    self.assertIn("only the named aster.agent_inference check", value)

    def test_rejects_naive_timestamp(self):
        case = dict(self.fixture["cases"][0])
        case["observation"] = dict(case["observation"], observed_at="2026-01-01T00:00:00")
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            deterministic.answer(case)

    def test_rejects_changed_fact_scope(self):
        case = dict(self.fixture["cases"][0])
        case["observation"] = dict(case["observation"], facts={"check_id": "all"})
        with self.assertRaisesRegex(ValueError, "fact boundary"):
            deterministic.answer(case)


if __name__ == "__main__":
    unittest.main()
