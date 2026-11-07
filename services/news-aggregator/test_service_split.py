import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ServiceSplitTests(unittest.TestCase):
    def test_digest_hands_narration_to_independent_unit(self):
        wrapper = (ROOT / "run_digest.sh").read_text()
        self.assertIn(
            "systemctl start --no-block news-aggregator-audio.service", wrapper
        )
        self.assertNotIn("audio_digest.py", wrapper)

    def test_audio_unit_has_no_digest_lifecycle_dependency(self):
        unit = (ROOT / "news-aggregator-audio.service").read_text()
        self.assertIn("EnvironmentFile=/etc/news-aggregator/aster-voice.env", unit)
        self.assertIn("audio_digest.py", unit)
        for directive in ("PartOf=", "BindsTo=", "Requires=news-aggregator-digest"):
            self.assertNotIn(directive, unit)


if __name__ == "__main__":
    unittest.main()
