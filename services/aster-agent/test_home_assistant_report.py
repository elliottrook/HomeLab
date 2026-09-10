import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from home_assistant_report import get_home_assistant_report


class HomeAssistantReportTests(unittest.TestCase):
    def _report(self, generated_at: datetime) -> dict:
        return {
            "schema_version": 1,
            "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
            "domains": {
                "light": {
                    "status": "warning",
                    "coverage": ["state"],
                    "entity_total": 12,
                    "entity_on": 4,
                    "entity_off": 7,
                    "entity_unavailable": 1,
                    "entity_unknown": 0,
                }
            },
        }

    def _read(self, report: dict, now: datetime) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            return get_home_assistant_report(path, now=now)

    def test_returns_only_aggregate_values_from_fresh_report(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        result = self._read(self._report(now - timedelta(minutes=2)), now)
        self.assertEqual(result["domains"]["light"]["entity_unavailable"], 1)
        self.assertNotIn("error", result)

    def test_rejects_stale_report(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        result = self._read(self._report(now - timedelta(minutes=16)), now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("stale", result["error"])

    def test_rejects_future_report(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        result = self._read(self._report(now + timedelta(seconds=1)), now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("stale", result["error"])

    def test_rejects_unapproved_field_that_could_carry_private_data(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        report = self._report(now)
        report["domains"]["light"]["entity_id"] = "light.living_room_lamp"
        result = self._read(report, now)
        self.assertEqual(result["status"], "unavailable")

    def test_rejects_unapproved_top_level_field(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        report = self._report(now)
        report["long_lived_token"] = "not permitted"
        result = self._read(report, now)
        self.assertEqual(result["status"], "unavailable")

    def test_rejects_unknown_domain(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        report = self._report(now)
        report["domains"]["person"] = report["domains"].pop("light")
        result = self._read(report, now)
        self.assertEqual(result["status"], "unavailable")

    def test_rejects_counts_in_an_uncovered_domain(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        report = self._report(now)
        report["domains"]["light"]["coverage"] = []
        result = self._read(report, now)
        self.assertEqual(result["status"], "unavailable")

    def test_allows_honest_uncovered_domain_with_null_counters(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        report = self._report(now)
        domain = report["domains"]["light"]
        domain["status"] = "failed"
        domain["coverage"] = []
        for field in ("entity_total", "entity_on", "entity_off", "entity_unavailable", "entity_unknown"):
            domain[field] = None
        result = self._read(report, now)
        self.assertEqual(result["domains"]["light"]["coverage"], [])
        self.assertIsNone(result["domains"]["light"]["entity_total"])

    def test_rejects_inconsistent_domain_counts(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        report = self._report(now)
        report["domains"]["light"]["entity_total"] = 99
        result = self._read(report, now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("inconsistent", result["error"])

    def test_rejects_negative_or_oversized_count(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        report = self._report(now)
        report["domains"]["light"]["entity_on"] = -1
        result = self._read(report, now)
        self.assertEqual(result["status"], "unavailable")

    def test_rejects_malformed_json(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            path.write_text("{not json", encoding="utf-8")
            result = get_home_assistant_report(path, now=now)
        self.assertEqual(result["status"], "unavailable")

    def test_rejects_oversized_report(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            path.write_text("x" * 65_537, encoding="utf-8")
            result = get_home_assistant_report(path, now=now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("maximum", result["error"])

    def test_rejects_group_writable_report(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            path.write_text(json.dumps(self._report(now)), encoding="utf-8")
            path.chmod(0o664)
            result = get_home_assistant_report(path, now=now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("writable", result["error"])

    def test_rejects_symlink_report(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text(json.dumps(self._report(now)), encoding="utf-8")
            path = root / "latest.json"
            path.symlink_to(target)
            result = get_home_assistant_report(path, now=now)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("regular", result["error"])


if __name__ == "__main__":
    unittest.main()
