import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
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
            self.assertEqual(report["repair_candidates"], [])
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)

    def test_failed_queue_call_does_not_write_error_detail(self):
        with patch.object(producer, "docker_running", return_value=True), patch.object(
            producer, "arr_queue", side_effect=RuntimeError("secret response")
        ):
            result = producer.service_report("radarr")
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("secret", json.dumps(result))

    def test_candidate_mapping_is_reduced_to_one_fresh_opaque_reference(self):
        now = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        state = {
            "candidates": [
                {
                    "reference": "radarr-q-abcdefghijklmnop",
                    "queue_id": 42,
                    "issued_at": now.isoformat(),
                    "expires_at": (now + timedelta(minutes=5)).isoformat(),
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.json"
            path.write_text(json.dumps(state), encoding="utf-8")
            result = producer.repair_candidates(path, now=now)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["candidate_ref"], "radarr-q-abcdefghijklmnop")
        self.assertNotIn("queue_id", result[0])
        self.assertNotIn("42", json.dumps(result))

    def test_expired_malformed_or_multiple_candidates_fail_closed(self):
        now = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.json"
            for payload in (
                {"candidates": []},
                {"candidates": [{"reference": "42"}]},
                {"candidates": [{}, {}]},
            ):
                path.write_text(json.dumps(payload), encoding="utf-8")
                self.assertEqual(producer.repair_candidates(path, now=now), [])

    def test_writable_or_symlinked_candidate_state_fails_closed(self):
        now = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
        payload = {
            "candidates": [
                {
                    "reference": "radarr-q-abcdefghijklmnop",
                    "queue_id": 42,
                    "issued_at": now.isoformat(),
                    "expires_at": (now + timedelta(minutes=5)).isoformat(),
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "candidate-target.json"
            target.write_text(json.dumps(payload), encoding="utf-8")
            target.chmod(0o664)
            self.assertEqual(producer.repair_candidates(target, now=now), [])

            target.chmod(0o600)
            symlink = root / "candidate-link.json"
            symlink.symlink_to(target)
            self.assertEqual(producer.repair_candidates(symlink, now=now), [])


if __name__ == "__main__":
    unittest.main()
