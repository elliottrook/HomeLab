import unittest

from aster_household_contract import decide


STATE = {
    "timers": ["pasta"],
    "rooms": ["kitchen", "office"],
    "entities": ["kitchen lights", "office lamp"],
    "media_available": True,
}


class HouseholdContractTests(unittest.TestCase):
    def test_explicit_timer(self):
        self.assertEqual(decide("Set an egg timer for 6.5 minutes", STATE)["effect"]["seconds"], 390)

    def test_conflicting_timer_has_no_effect(self):
        result = decide("Set a timer for 5 minutes, make that 10 minutes", STATE)
        self.assertEqual((result["status"], result["effect"]), ("clarify", None))

    def test_ambiguous_alarm_has_no_effect(self):
        result = decide("Set an alarm for four o'clock", STATE)
        self.assertEqual((result["status"], result["effect"]), ("clarify", None))

    def test_exact_timer_cancel(self):
        self.assertEqual(decide("Cancel the pasta timer", STATE)["effect"]["label"], "pasta")

    def test_media_target(self):
        result = decide("Play jazz in kitchen", STATE)
        self.assertEqual(result["effect"], {"capability": "media.play", "query": "jazz", "target": "kitchen"})

    def test_unavailable_media_has_no_effect(self):
        state = dict(STATE, media_available=False)
        self.assertIsNone(decide("Play jazz in kitchen", state)["effect"])

    def test_missing_media_target_clarifies(self):
        self.assertEqual(decide("Play jazz", STATE)["status"], "clarify")

    def test_exact_home_control(self):
        result = decide("Turn off the kitchen lights", STATE)
        self.assertEqual(result["effect"]["state"], "off")

    def test_unknown_device_has_no_effect(self):
        result = decide("Turn on the lamp", STATE)
        self.assertIsNone(result["effect"])

    def test_unrelated_request_is_unsupported(self):
        self.assertEqual(decide("Summarize my inbox", STATE)["status"], "unsupported")


if __name__ == "__main__":
    unittest.main()
