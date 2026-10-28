import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backup_catalogue_incident_adapter import read_backup_catalogue_observation


NOW = datetime(2026, 10, 28, 23, 0, tzinfo=timezone.utc)


class BackupCatalogueIncidentAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.aggregate = root / "aggregate.json"
        self.catalogue = root / "catalogue.json"

    def write_pair(self, *, state="pass", status="healthy", observed=None):
        observed = observed or NOW - timedelta(seconds=30)
        aggregate = {
            "schema": 1, "generated_at": observed.isoformat(), "status": status,
            "checks": [{"name": "HomeLab Doctor", "status": "pass", "summary": "private backup detail"}],
        }
        raw = (json.dumps(aggregate, sort_keys=True, separators=(",", ":")) + "\n").encode()
        self.aggregate.write_bytes(raw)
        catalogue = {
            "schema": 3, "generated_at": aggregate["generated_at"], "run_id": "a" * 32,
            "source_report_digest": hashlib.sha256(raw).hexdigest(),
            "checks": [
                {"check_id": "aster.agent_inference", "state": "pass"},
                {"check_id": "aster.speech", "state": "pass"},
                {"check_id": "backup.protection", "state": state},
            ],
        }
        self.catalogue.write_text(json.dumps(catalogue))
        self.aggregate.chmod(0o600)
        self.catalogue.chmod(0o600)
        return catalogue

    def read(self):
        return read_backup_catalogue_observation(
            "incident-backup-fixture", self.aggregate, self.catalogue, NOW,
            required_uid=os.getuid(),
        )

    def test_projects_only_backup_state_without_summary(self):
        self.write_pair(state="fail", status="failed")
        observation = self.read()
        self.assertEqual(("backup-catalog", "backup", "fail"), (
            observation.target, observation.kind, observation.state,
        ))
        self.assertEqual("backup.protection", observation.facts["check_id"])
        self.assertNotIn("private backup detail", json.dumps(observation.__dict__))

    def test_all_source_states_map_or_abstain(self):
        for source_state, expected, status in (
            ("pass", "ok", "healthy"), ("warn", "warn", "warning"),
            ("fail", "fail", "failed"), ("unavailable", "unavailable", "healthy"),
        ):
            with self.subTest(source_state=source_state):
                self.write_pair(state=source_state, status=status)
                self.assertEqual(expected, self.read().state)

    def test_tamper_stale_permissions_and_missing_check_abstain(self):
        value = self.write_pair()
        value["source_report_digest"] = "0" * 64
        self.catalogue.write_text(json.dumps(value))
        self.assertEqual("unavailable", self.read().state)
        self.write_pair(observed=NOW - timedelta(hours=37))
        self.assertEqual("unavailable", self.read().state)
        self.write_pair()
        self.catalogue.chmod(0o666)
        self.assertEqual("unavailable", self.read().state)
        value = self.write_pair()
        value["checks"] = value["checks"][:2]
        self.catalogue.write_text(json.dumps(value))
        self.assertEqual("unavailable", self.read().state)


if __name__ == "__main__":
    unittest.main()
