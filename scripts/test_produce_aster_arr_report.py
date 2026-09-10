import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("aster_arr_producer", ROOT / "scripts/produce-aster-arr-report.py")
producer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(producer)


class ProducerTests(unittest.TestCase):
    def test_writes_aggregate_report_without_import_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reports/latest.json"
            with (
                patch.object(producer, "REPORT_PATH", path),
                patch.object(producer, "docker_running", return_value=True),
                patch.object(producer, "arr_queue", return_value=(3, 1)),
                patch.object(producer, "sabnzbd_queue", return_value=(2, 0)),
            ):
                self.assertEqual(producer.main(), 0)
            report = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(report["services"]["radarr"]["queue_pending"], 3)
            self.assertEqual(report["services"]["radarr"]["import_pending"], None)
            self.assertEqual(report["services"]["prowlarr"]["coverage"], ["health"])
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)

    def test_failed_queue_call_does_not_write_error_detail(self):
        with patch.object(producer, "docker_running", return_value=True), patch.object(
            producer, "arr_queue", side_effect=RuntimeError("secret response")
        ):
            result = producer.service_report("radarr")
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("secret", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
