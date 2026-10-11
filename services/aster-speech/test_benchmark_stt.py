import json
import tempfile
import unittest
import wave
from pathlib import Path

from benchmark_stt import Fixture, edit_distance, load_fixtures, normalize, run, summarize


class FakeTranscriber:
    name = "fake"
    load_seconds = 0.1

    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = 0

    def transcribe(self, audio):
        self.calls += 1
        return next(self.outputs)


def write_wav(path: Path, seconds: float = 1.0):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(b"\x00\x00" * int(16000 * seconds))


class FixtureTests(unittest.TestCase):
    def test_repository_fixtures_cover_required_household_names(self):
        fixtures = load_fixtures(Path(__file__).with_name("stt_benchmark_fixtures.json"))
        text = " ".join(fixture.text for fixture in fixtures)
        self.assertIn("Home Assistant", text)
        self.assertIn("Lutron Caseta", text)
        self.assertIn("British Columbia", text)

    def test_rejects_extra_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixtures.json"
            path.write_text(json.dumps([{
                "id": "one", "category": "test", "audio": "one.wav",
                "text": "hello", "transcript": "must not be separate",
            }]))
            with self.assertRaises(ValueError):
                load_fixtures(path)


class AccuracyTests(unittest.TestCase):
    def test_normalization_and_word_error_distance(self):
        self.assertEqual(normalize("Jason’s room!"), ["jason's", "room"])
        self.assertEqual(edit_distance(["home", "assistant"], ["home", "assist"]), 1)

    def test_results_exclude_recognized_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_wav(root / "one.wav")
            fixture = Fixture("one", "test", "one.wav", "Home Assistant")
            runner = FakeTranscriber(["warmup", "Home Assistant", "Home assist"])
            samples = run(runner, [fixture], root, warmups=1, iterations=2)
            self.assertEqual(runner.calls, 3)
            self.assertTrue(samples[0].exact)
            self.assertEqual(samples[1].word_errors, 1)
            self.assertNotIn("text", samples[0].__dict__)
            self.assertEqual(summarize(samples)["word_error_rate"], 0.25)

    def test_missing_audio_is_rejected_before_transcription(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture("one", "test", "missing.wav", "Hello")
            runner = FakeTranscriber([])
            with self.assertRaises(FileNotFoundError):
                run(runner, [fixture], Path(tmp), warmups=0, iterations=1)
            self.assertEqual(runner.calls, 0)


if __name__ == "__main__":
    unittest.main()
