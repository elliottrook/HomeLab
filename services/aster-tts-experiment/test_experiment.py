import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import wave


ROOT = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("experiment", ROOT / "experiment.py")
experiment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(experiment)


class ExperimentTests(unittest.TestCase):
    def test_fixed_corpus_is_valid_and_targeted(self):
        corpus = experiment.load_corpus(ROOT / "corpus.json")
        self.assertEqual(len(corpus["passages"]), 6)
        homographs = next(item for item in corpus["passages"] if item["id"] == "homographs")
        self.assertIn("produce", homographs["targets"])

    def test_private_corpus_text_is_rejected(self):
        corpus = json.loads((ROOT / "corpus.json").read_text())
        corpus["passages"][0]["source_class"] = "private"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.json"
            path.write_text(json.dumps(corpus))
            with self.assertRaisesRegex(ValueError, "private text"):
                experiment.load_corpus(path)

    def test_prepare_records_contract_and_unit_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = root / "voice_contract.py"
            contract.write_text(
                "from dataclasses import dataclass\n"
                "@dataclass\n"
                "class ContractMarker: value: str = 'production-shaped'\n"
                "def normalize_for_speech(text): return ' '.join(text.split())\n"
                "def semantic_units(text): return [text[i:i+200] for i in range(0, len(text), 200)]\n"
            )
            output = root / "plan.json"
            plan = experiment.prepare(ROOT / "corpus.json", contract, output)
            self.assertEqual(plan["schema"], experiment.PLAN_SCHEMA)
            self.assertEqual(len(plan["passages"]), 6)
            self.assertEqual(experiment.sha256_file(output), experiment.sha256_file(output))

    def test_wav_contract_rejects_wrong_sample_rate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.wav"
            with wave.open(str(path), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(16_000)
                audio.writeframes(b"\0\0" * 100)
            with self.assertRaisesRegex(ValueError, "contract mismatch"):
                experiment.inspect_wav(path)

    def test_blind_requires_two_unique_configs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = root / "plan.json"
            plan.write_text(json.dumps({"schema": experiment.PLAN_SCHEMA}))
            report = root / "report.json"
            report.write_text(json.dumps({
                "schema": experiment.REPORT_SCHEMA,
                "plan_sha256": experiment.sha256_file(plan),
                "config": {"id": "same"},
                "results": [],
            }))
            with self.assertRaisesRegex(ValueError, "two unique"):
                experiment.blind(plan, [report], root / "blind", 7)


if __name__ == "__main__":
    unittest.main()
