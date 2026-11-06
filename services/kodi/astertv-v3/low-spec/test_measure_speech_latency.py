import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure_speech_latency as subject


class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *_): return False


class SpeechLatencyTests(unittest.TestCase):
    def opener(self, request, timeout):
        self.assertEqual(timeout, 60)
        if request.full_url.endswith("/health"):
            return Response(json.dumps(subject.EXPECTED_HEALTH).encode())
        if request.full_url.endswith("/v1/tts"):
            return Response(b"RIFF" + b"\0" * 4 + b"WAVE" + b"\0" * 2048)
        if request.full_url.endswith("/v1/stt"):
            return Response(json.dumps({"text": subject.FIXTURE_TEXT}).encode())
        raise AssertionError(request.full_url)

    def test_content_free_success(self):
        with patch.object(subject.time, "monotonic", side_effect=[0, .2, .2, .4, .4, .6]):
            result = subject.run(3, opener=self.opener, hostname=subject.HOST, key="k" * 40)
        self.assertEqual(result["outcome"], "pass")
        self.assertEqual(result["exact"], 3)
        self.assertNotIn("text", json.dumps(result))
        self.assertFalse(result["retained_audio"])
        self.assertFalse(result["retained_transcript"])

    def test_wrong_target_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "speech-target"):
            subject.run(3, opener=self.opener, hostname="wrong", key="k" * 40)

    def test_authority_drift_fails_closed(self):
        def opener(request, timeout):
            value = dict(subject.EXPECTED_HEALTH); value["stt_model"] = "legacy"
            return Response(json.dumps(value).encode())
        with self.assertRaisesRegex(RuntimeError, "speech-authority-drift"):
            subject.run(3, opener=opener, hostname=subject.HOST, key="k" * 40)

    def test_percentile_is_nearest_rank(self):
        self.assertEqual(subject.percentile([1, 2, 3, 4, 5], .95), 5)


if __name__ == "__main__":
    unittest.main()
