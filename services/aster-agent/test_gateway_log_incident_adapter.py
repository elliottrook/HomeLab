import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from gateway_log_incident_adapter import read_gateway_log_observation


NOW = datetime(2026, 10, 28, 23, 30, tzinfo=timezone.utc)


class GatewayLogIncidentAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "report.json"

    def write(self, *, count=0, observed=None, **changes):
        value = {
            "schema": 1, "source": "aster-agent-journal",
            "generated_at": (observed or NOW - timedelta(seconds=30)).isoformat(),
            "window_seconds": 900, "high_priority_event_count": count,
            "truncated": False,
        }
        value.update(changes)
        self.path.write_text(json.dumps(value))
        self.path.chmod(0o600)

    def read(self):
        return read_gateway_log_observation(
            "incident-log-fixture", self.path, NOW, required_uid=os.getuid()
        )

    def test_zero_and_nonzero_counts_have_bounded_semantics(self):
        self.write()
        empty = self.read()
        self.assertEqual(("aster-gateway", "log", "ok"), (
            empty.target, empty.kind, empty.state,
        ))
        self.assertEqual(0, empty.facts["high_priority_event_count"])
        self.write(count=2)
        warning = self.read()
        self.assertEqual("warn", warning.state)
        self.assertEqual(2, warning.facts["high_priority_event_count"])
        self.assertEqual(24, len(warning.facts["report_digest"]))

    def test_malformed_stale_permissions_link_and_extra_field_abstain(self):
        self.write(extra="private")
        self.assertEqual("unavailable", self.read().state)
        self.write(observed=NOW - timedelta(minutes=31))
        self.assertEqual("unavailable", self.read().state)
        self.write()
        self.path.chmod(0o622)
        self.assertEqual("unavailable", self.read().state)
        self.path.unlink()
        target = Path(self.temporary.name) / "target.json"
        target.write_text("{}")
        self.path.symlink_to(target)
        self.assertEqual("unavailable", self.read().state)


if __name__ == "__main__":
    unittest.main()
