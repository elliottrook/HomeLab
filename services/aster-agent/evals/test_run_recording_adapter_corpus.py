import json
import unittest
from pathlib import Path

from run_recording_adapter_corpus import run


FIXTURE = Path(__file__).with_name("aster-recording-adapter-v1.json")


class RecordingAdapterCorpusTests(unittest.TestCase):
    def test_sealed_corpus_passes_without_effects(self):
        report = run(json.loads(FIXTURE.read_text()))
        self.assertEqual(report["pass_count"], report["case_count"])
        self.assertEqual(report["effect_count"], 0)
        self.assertTrue(all(call["effect_permitted"] is False
                            for result in report["results"] for call in result["recorded_calls"]))

    def test_unsealed_corpus_is_rejected(self):
        suite = json.loads(FIXTURE.read_text())
        suite["status"] = "draft"
        with self.assertRaises(ValueError):
            run(suite)


if __name__ == "__main__":
    unittest.main()
