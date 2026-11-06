import unittest

from capacity import estimate


class CapacityTests(unittest.TestCase):
    def test_current_renderer_is_not_twice_daily_viable(self):
        fifteen = estimate(15)
        twenty = estimate(20)
        self.assertGreater(fifteen["video_render_hours"], 42)
        self.assertGreater(twenty["video_render_hours"], 57)
        self.assertGreater(twenty["serial_total_hours"] * 2, 114)

    def test_qwen_timing_uses_measured_render_factor(self):
        self.assertEqual(estimate(15)["tts_minutes"], 12.97)
        self.assertEqual(estimate(20)["tts_minutes"], 17.3)


if __name__ == "__main__":
    unittest.main()
