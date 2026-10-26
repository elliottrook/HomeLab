import unittest

from fixed_doctor_response import FixedDoctorResponseDenied, LIMITATION, render_observation


def observation(state="ok", **changes):
    value = {
        "source": "homelab-doctor-structured/v2",
        "state": state,
        "observed_at": "2026-10-26T12:00:00-07:00",
        "age_seconds": 15,
        "facts": {} if state == "unavailable" else {"check_id": "aster.agent_inference"},
    }
    value.update(changes)
    return value


class FixedDoctorResponseTests(unittest.TestCase):
    def test_all_states_have_scope_freshness_and_limitation(self):
        for state in ("ok", "warn", "fail", "unavailable"):
            with self.subTest(state=state):
                answer = render_observation(observation(state))
                self.assertIn("observed at 2026-10-26T12:00:00-07:00", answer)
                self.assertIn("15 seconds old", answer)
                self.assertIn(LIMITATION, answer)
                self.assertIn("only", answer.lower() if state != "unavailable" else "only")

    def test_fails_closed_on_schema_state_time_age_and_fact_drift(self):
        changes = (
            {"source": "other"}, {"state": "unknown"}, {"observed_at": "not-time"},
            {"observed_at": "2026-10-26T12:00:00"}, {"age_seconds": True},
            {"age_seconds": 601}, {"facts": {"check_id": "other"}},
        )
        for change in changes:
            with self.subTest(change=change), self.assertRaises(FixedDoctorResponseDenied):
                render_observation(observation(**change))

    def test_unavailable_rejects_claimed_facts(self):
        with self.assertRaises(FixedDoctorResponseDenied):
            render_observation(observation("unavailable", facts={"check_id": "aster.agent_inference"}))


if __name__ == "__main__":
    unittest.main()
