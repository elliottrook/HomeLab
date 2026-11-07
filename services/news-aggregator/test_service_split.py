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

    def test_text_jobs_require_bounded_loopback_cpu_llm(self):
        unit = (ROOT / "news-aggregator-cpu-llama.service").read_text()
        dependency = (ROOT / "news-aggregator-local-llm.conf").read_text()
        self.assertIn("--host 127.0.0.1 --port 11436", unit)
        self.assertIn("-ngl 0", unit)
        self.assertIn("MemoryMax=10G", unit)
        self.assertIn("MemorySwapMax=0", unit)
        self.assertIn("CPUQuota=800%", unit)
        self.assertIn("Requires=news-aggregator-cpu-llama.service", dependency)
        self.assertIn("NEWS_LLM_URL=http://127.0.0.1:11436", dependency)

    def test_text_clients_default_to_local_cpu_authority(self):
        for name in ("digest.py", "summarize.py", "language_notes.py"):
            source = (ROOT / name).read_text()
            self.assertIn('"NEWS_LLM_URL"', source)
            self.assertIn("http://127.0.0.1:11436/v1/chat/completions", source)
            self.assertNotIn("192.168.70.12:11435", source)


if __name__ == "__main__":
    unittest.main()
