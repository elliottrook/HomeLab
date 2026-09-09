import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from arr_report import get_arr_report


class ArrReportTests(unittest.TestCase):
    def _report(self, generated_at: datetime) -> dict:
        return {
            "schema_version": 1,
            "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
            "services": {
                "radarr": {
                    "status": "warning",
                    "coverage": ["health", "queue", "import"],
                    "queue_pending": 2,
                    "queue_errors": 1,
                    "import_pending": 0,
                    "import_errors": 0,
                }
            },
        }

    def _read(self, report: dict, now: datetime) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            return get_arr_report(path, now=now)

    def test_returns_only_aggregate_values_from_fresh_report(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        result = self._read(self._report(now - timedelta(minutes=2)), now)
        self.assertEqual(result["services"]["radarr"]["queue_errors"], 1)
        self.assertNotIn("error", result)

    def test_rejects_stale_report(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        result = self._read(self._report(now - timedelta(minutes=16)), now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("stale", result["error"])

    def test_rejects_future_report(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        result = self._read(self._report(now + timedelta(seconds=1)), now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("stale", result["error"])

    def test_rejects_unapproved_field_that_could_carry_private_data(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        report = self._report(now)
        report["services"]["radarr"]["raw_error"] = "private title / path"
        result = self._read(report, now)
        self.assertEqual(result["status"], "unavailable")

    def test_rejects_unapproved_top_level_field(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        report = self._report(now)
        report["credential"] = "not permitted"
        result = self._read(report, now)
        self.assertEqual(result["status"], "unavailable")

    def test_rejects_unknown_service_and_nonaggregate_counter(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        report = self._report(now)
        report["services"]["unknown"] = report["services"].pop("radarr")
        result = self._read(report, now)
        self.assertEqual(result["status"], "unavailable")

    def test_allows_honest_partial_coverage_only_with_null_counters(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        report = self._report(now)
        service = report["services"]["radarr"]
        service["coverage"] = ["health", "queue"]
        service["import_pending"] = None
        service["import_errors"] = None
        result = self._read(report, now)
        self.assertEqual(result["services"]["radarr"]["coverage"], ["health", "queue"])

    def test_rejects_counts_in_an_uncovered_scope(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        report = self._report(now)
        report["services"]["radarr"]["coverage"] = ["health", "queue"]
        result = self._read(report, now)
        self.assertEqual(result["status"], "unavailable")

    def test_rejects_malformed_json(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            path.write_text("{not json", encoding="utf-8")
            result = get_arr_report(path, now=now)
        self.assertEqual(result["status"], "unavailable")

    def test_rejects_oversized_report(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            path.write_text("x" * 65_537, encoding="utf-8")
            result = get_arr_report(path, now=now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("maximum", result["error"])

    def test_rejects_group_writable_report(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            path.write_text(json.dumps(self._report(now)), encoding="utf-8")
            path.chmod(0o664)
            result = get_arr_report(path, now=now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("writable", result["error"])

    def test_rejects_symlink_report(self):
        now = datetime(2026, 9, 9, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text(json.dumps(self._report(now)), encoding="utf-8")
            path = root / "latest.json"
            path.symlink_to(target)
            result = get_arr_report(path, now=now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("regular", result["error"])


if __name__ == "__main__":
    unittest.main()
