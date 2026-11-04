import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave


SCRIPT = Path(__file__).parents[1] / "tools" / "run_b60_shadow.py"
SPEC = importlib.util.spec_from_file_location("run_b60_shadow", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class B60ShadowTests(unittest.TestCase):
    @staticmethod
    def wav(seconds):
        result = io.BytesIO()
        with wave.open(result, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(24000)
            audio.writeframes(b"\0\0" * int(seconds * 24000))
        return result.getvalue()

    def test_render_and_resume_completed_chapter(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            job = {
                "schema": 1, "pilot_id": "a" * 32, "book_id": 1,
                "source_sha256": "b" * 64, "sample_rate": 24000,
                "voice": "bm_daniel", "speed": 0.95,
                "chapters": [{"index": 1, "text": "Synthetic chapter.",
                              "text_sha256": "c" * 64, "units": []}],
            }
            job_path = root / "job.json"
            job_path.write_text(json.dumps(job), encoding="utf-8")
            fake_wav = self.wav(1)
            with patch.object(MODULE, "_audio", return_value=fake_wav) as render:
                result = MODULE.run(job_path, root / "output", "http://loopback", 1)
            self.assertEqual("rendered", result["state"])
            self.assertEqual(1, render.call_count)
            manifest = root / "output" / ("a" * 32) / "manifest.json"
            manifest.unlink()
            with patch.object(MODULE, "_audio", side_effect=AssertionError("rerendered")):
                resumed = MODULE.run(job_path, root / "output", "http://loopback", 1)
            self.assertEqual("rendered", resumed["state"])

    def test_rejects_implausibly_slow_candidate_before_writing_audio(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            text = " ".join(["word"] * 60)
            job = {
                "schema": 1, "pilot_id": "d" * 32, "book_id": 1,
                "source_sha256": "e" * 64, "sample_rate": 24000,
                "voice": "bm_daniel", "speed": 0.95,
                "chapters": [{"index": 1, "text": text,
                              "text_sha256": "f" * 64, "units": []}],
            }
            job_path = root / "job.json"
            job_path.write_text(json.dumps(job), encoding="utf-8")
            with patch.object(MODULE, "_audio", return_value=self.wav(60)):
                with self.assertRaisesRegex(ValueError, "pilot-pacing"):
                    MODULE.run(job_path, root / "output", "http://loopback", 1)
            result = root / "output" / ("d" * 32)
            self.assertTrue((result / "FAILED").exists())
            self.assertFalse((result / "chapters" / "0001.wav").exists())


if __name__ == "__main__":
    unittest.main()
