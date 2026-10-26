import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from speech_catalogue_incident_adapter import read_speech_catalogue_observation


NOW = datetime(2026, 10, 26, 21, 0, tzinfo=timezone.utc)


class SpeechCatalogueIncidentAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.aggregate = self.root / "aggregate.json"
        self.catalogue = self.root / "catalogue.json"

    def write_pair(self, *, state="pass", status="healthy", observed=None):
        observed = observed or NOW - timedelta(seconds=30)
        aggregate = {
            "schema": 1,
            "generated_at": observed.isoformat(),
            "status": status,
            "checks": [{"name": "HomeLab Doctor", "status": "pass", "summary": "private words"}],
        }
        raw = (json.dumps(aggregate, sort_keys=True, separators=(",", ":")) + "\n").encode()
        self.aggregate.write_bytes(raw)
        catalogue = {
            "schema": 3,
            "generated_at": aggregate["generated_at"],
            "run_id": "a" * 32,
            "source_report_digest": hashlib.sha256(raw).hexdigest(),
            "checks": [
                {"check_id": "aster.agent_inference", "state": "pass"},
                {"check_id": "aster.speech", "state": state},
            ],
        }
        self.catalogue.write_text(json.dumps(catalogue), encoding="utf-8")
        self.aggregate.chmod(0o600)
        self.catalogue.chmod(0o600)
        return catalogue

    def read(self):
        return read_speech_catalogue_observation(
            "incident-1", self.aggregate, self.catalogue, NOW,
            required_uid=os.getuid(),
        )

    def test_projects_only_named_speech_state_without_summary(self):
        self.write_pair(state="fail", status="failed")
        value = self.read().validate(NOW)
        self.assertEqual("fail", value["state"])
        self.assertEqual("homelab-doctor-catalogue/v3", value["source"])
        self.assertEqual("homelab-doctor", value["target"])
        self.assertEqual("aster.speech", value["facts"]["check_id"])
        self.assertNotIn("private words", json.dumps(value))

    def test_all_source_states_map_or_abstain(self):
        for source_state, expected, status in (
            ("pass", "ok", "healthy"), ("warn", "warn", "warning"),
            ("fail", "fail", "failed"), ("unavailable", "unavailable", "healthy"),
        ):
            with self.subTest(source_state=source_state):
                self.write_pair(state=source_state, status=status)
                self.assertEqual(expected, self.read().validate(NOW)["state"])

    def test_digest_time_shape_duplicate_and_contradiction_abstain(self):
        mutations = []
        value = self.write_pair()
        mutations.append(lambda: self.catalogue.write_text(json.dumps({**value, "source_report_digest": "0" * 64})))
        mutations.append(lambda: self.catalogue.write_text(json.dumps({**value, "generated_at": NOW.isoformat()})))
        mutations.append(lambda: self.catalogue.write_text(json.dumps({**value, "extra": True})))
        mutations.append(lambda: self.catalogue.write_text(self.catalogue.read_text().replace('"schema": 3', '"schema": 3, "schema": 3')))
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                value = self.write_pair()
                mutate()
                self.assertEqual("unavailable", self.read().state)
        self.write_pair(state="fail", status="healthy")
        self.assertEqual("unavailable", self.read().state)

    def test_stale_future_permissions_symlink_and_hardlink_abstain(self):
        for observed in (NOW - timedelta(hours=37), NOW + timedelta(seconds=1)):
            with self.subTest(observed=observed):
                self.write_pair(observed=observed)
                self.assertEqual("unavailable", self.read().state)
        self.write_pair()
        self.catalogue.chmod(0o666)
        self.assertEqual("unavailable", self.read().state)
        self.write_pair()
        original = self.catalogue
        linked = self.root / "catalogue-link.json"
        linked.symlink_to(original)
        self.catalogue = linked
        self.assertEqual("unavailable", self.read().state)
        self.catalogue = original
        hardlink = self.root / "catalogue-hardlink.json"
        os.link(original, hardlink)
        self.assertEqual("unavailable", self.read().state)

    def test_absent_fixed_check_and_unknown_catalogue_entry_abstain(self):
        value = self.write_pair()
        value["checks"] = value["checks"][:1]
        self.catalogue.write_text(json.dumps(value))
        self.assertEqual("unavailable", self.read().state)
        value = self.write_pair()
        value["checks"].append({"check_id": "Invalid Check", "state": "pass"})
        self.catalogue.write_text(json.dumps(value))
        self.assertEqual("unavailable", self.read().state)


if __name__ == "__main__":
    unittest.main()
