from datetime import date
import unittest

from studio import build_review_request, load_studio, review_due, verify_assets


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_studio()

    def test_studio_and_brand_assets_are_pinned(self):
        verify_assets(self.profile)

    def test_first_review_is_due_on_2027_anniversary(self):
        self.assertFalse(review_due(self.profile, date(2027, 11, 5)))
        self.assertTrue(review_due(self.profile, date(2027, 11, 6)))

    def test_review_uses_current_brand_snapshot_and_remains_candidate(self):
        request = build_review_request(self.profile, date(2027, 11, 6))
        self.assertEqual(request["status"], "candidate")
        self.assertFalse(request["activate_automatically"])
        self.assertEqual(len(request["brand_snapshot"]["members"]), 4)
        self.assertIn("then-current accepted AsterTV", request["required_steps"][0])

    def test_studio_keeps_tv_and_fallback_invariants(self):
        contract = self.profile["design_contract"]
        self.assertEqual(contract["target_canvas"], "1920x1080")
        self.assertTrue(contract["tv_viewing_distance_required"])
        self.assertTrue(contract["preserve_audio_text_fallback"])
        self.assertFalse(contract["baked_text"])
        self.assertIn("traditional horizontal rectangle", contract["story_monitor_geometry"])


if __name__ == "__main__":
    unittest.main()
