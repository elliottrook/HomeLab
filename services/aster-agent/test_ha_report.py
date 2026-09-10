import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ha_report import get_ha_report


class HomeAssistantReportTests(unittest.TestCase):
    def report(self, now):
        return {"schema_version": 1, "generated_at": now.isoformat(),
                "core": {"status": "healthy", "version": "2026.9.1", "latest_version": "2026.9.1", "update_available": False, "watchdog": True},
                "supervisor": {"status": "healthy", "version": "2026.09.0", "latest_version": "2026.09.0", "update_available": False, "supported": True, "healthy": True},
                "backup": {"mount_configured": True, "mount_active": True},
                "resolution": {"unsupported_count": 0, "unhealthy_count": 0, "issue_count": 0, "suggestion_count": 0}}

    def read(self, report, now):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            return get_ha_report(path, now=now)

    def test_accepts_fresh_exact_aggregate_report(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        self.assertEqual(self.read(self.report(now), now)["backup"]["mount_active"], True)

    def test_rejects_stale_report(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        self.assertEqual(self.read(self.report(now - timedelta(minutes=16)), now)["status"], "unavailable")

    def test_rejects_extra_private_field(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        report = self.report(now); report["entities"] = ["lock.front_door"]
        self.assertEqual(self.read(report, now)["status"], "unavailable")

    def test_rejects_symlink_and_writable_report(self):
        now = datetime(2026, 9, 10, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); target = root / "target"; target.write_text(json.dumps(self.report(now)))
            link = root / "latest.json"; link.symlink_to(target)
            self.assertEqual(get_ha_report(link, now=now)["status"], "unavailable")
            target.chmod(0o664)
            self.assertEqual(get_ha_report(target, now=now)["status"], "unavailable")
