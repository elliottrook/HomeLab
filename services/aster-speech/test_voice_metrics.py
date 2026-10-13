import unittest

from voice_metrics import VoiceMetrics


class VoiceMetricsTests(unittest.TestCase):
    def test_prometheus_output_is_bounded_and_content_free(self):
        metrics = VoiceMetrics()
        metrics.observe_request("interactive", "ok", 0.5)
        metrics.observe_queue("interactive", 0.1)
        metrics.render_errors["batch"] += 1
        metrics.cancellations["interactive"] += 1
        output = metrics.render()
        self.assertIn('aster_voice_requests_total{caller="interactive",outcome="ok"} 1', output)
        self.assertIn('aster_voice_request_duration_seconds_count{caller="interactive"} 1', output)
        self.assertIn('aster_voice_render_errors_total{caller="batch"} 1', output)
        self.assertNotIn("request_id", output)
        self.assertNotIn("submitted words", output)


if __name__ == "__main__":
    unittest.main()
