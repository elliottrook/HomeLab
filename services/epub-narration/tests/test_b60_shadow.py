import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "tools" / "run_b60_shadow.py"
SPEC = importlib.util.spec_from_file_location("run_b60_shadow", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class B60ShadowTests(unittest.TestCase):
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
            fake_wav = b"RIFF" + b"\0" * 4 + b"WAVE" + b"\0" * 64
            with patch.object(MODULE, "_audio", return_value=fake_wav) as render:
                result = MODULE.run(job_path, root / "output", "http://loopback", 1)
            self.assertEqual("rendered", result["state"])
            self.assertEqual(1, render.call_count)
            manifest = root / "output" / ("a" * 32) / "manifest.json"
            manifest.unlink()
            with patch.object(MODULE, "_audio", side_effect=AssertionError("rerendered")):
                resumed = MODULE.run(job_path, root / "output", "http://loopback", 1)
            self.assertEqual("rendered", resumed["state"])


if __name__ == "__main__":
    unittest.main()
