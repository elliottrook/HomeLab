import unittest

from fixed_speech_response import FixedSpeechResponseDenied, LIMITATION, render_observation


def observation(state="ok", **changes):
    value = {
        "source": "homelab-doctor-catalogue/v3",
        "state": state,
        "observed_at": "2026-10-26T20:00:00Z",
        "age_seconds": 30,
        "facts": {} if state == "unavailable" else {"check_id": "aster.speech"},
    }
    value.update(changes)
    return value


class FixedSpeechResponseTests(unittest.TestCase):
    def test_all_states_are_scoped_fresh_and_limited(self):
        for state in ("ok", "warn", "fail", "unavailable"):
            with self.subTest(state=state):
                answer = render_observation(observation(state))
                self.assertIn("2026-10-26T20:00:00Z", answer)
                self.assertIn("30 seconds old", answer)
                self.assertIn(LIMITATION, answer)
                self.assertIn("speech", answer.lower())

    def test_schema_source_state_time_age_and_facts_fail_closed(self):
        changes = (
            {"source": "other"}, {"state": "unknown"}, {"observed_at": "bad"},
            {"observed_at": "2026-10-26T20:00:00"}, {"age_seconds": True},
            {"age_seconds": 129601}, {"facts": {"check_id": "aster.agent_inference"}},
        )
        for change in changes:
            with self.subTest(change=change), self.assertRaises(FixedSpeechResponseDenied):
                render_observation(observation(**change))

    def test_source_valid_age_boundary_is_accepted(self):
        self.assertIn("129600 seconds old", render_observation(observation(age_seconds=129600)))

    def test_unavailable_cannot_claim_facts(self):
        with self.assertRaises(FixedSpeechResponseDenied):
            render_observation(observation("unavailable", facts={"check_id": "aster.speech"}))


if __name__ == "__main__":
    unittest.main()
