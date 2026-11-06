import hashlib
import json
from pathlib import Path
import unittest
import wave


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "pilot" / "pilot_manifest.json"


def resolve(asset: str) -> Path:
    return (MANIFEST.parent / asset).resolve()


class PilotManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_pilot_is_synthetic_candidate_and_not_production(self):
        self.assertEqual(self.manifest["status"], "candidate")
        self.assertEqual(self.manifest["scope"], "synthetic local evaluation only")
        self.assertFalse(self.manifest["production_enabled"])

    def test_source_audio_and_output_are_hash_pinned(self):
        records = (
            self.manifest["source"],
            {
                "asset": self.manifest["speech"]["wav_asset"],
                "sha256": self.manifest["speech"]["wav_sha256"],
            },
            self.manifest["output"],
        )
        for record in records:
            path = resolve(record["asset"])
            self.assertTrue(path.is_file(), path)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["sha256"])

    def test_audio_uses_canonical_contract(self):
        speech = self.manifest["speech"]
        self.assertEqual(speech["model"], "qwen3-tts-1.7b-base-q8-metal")
        self.assertEqual(speech["voice"], "aster")
        self.assertEqual(speech["language"], "English")
        self.assertEqual(speech["seed"], 20261104)
        with wave.open(str(resolve(speech["wav_asset"])), "rb") as wav_file:
            self.assertEqual(wav_file.getframerate(), 24000)
            self.assertEqual(wav_file.getnchannels(), 1)

    def test_motion_limit_is_explicit(self):
        motion = self.manifest["motion_contract"]
        self.assertFalse(motion["articulated_hands_or_arms"])
        self.assertTrue(motion["random_motion_not_yet_accepted"])
        self.assertIn("accepted", self.manifest["observations"]["human_lip_sync_assessment"])


if __name__ == "__main__":
    unittest.main()
