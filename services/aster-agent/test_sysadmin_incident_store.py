import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sysadmin_incident_store import IncidentStore, parse_producer_envelope
from sysadmin_investigation import EvidenceRequest, InvestigationError, create_incident


NOW = datetime(2026, 9, 28, 18, 0, tzinfo=timezone.utc)
FIXTURE = Path(__file__).with_name("evals") / "sysadmin-producer-fixture.json"


class ProducerAndStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = IncidentStore(Path(self.tmp.name) / "incidents.sqlite3")
        self.incident = create_incident("fixture-incident-001", "Fixture incident", [
            EvidenceRequest("aster-gateway", "status", "Establish gateway state."),
            EvidenceRequest("inference-server", "status", "Check the dependency."),
        ])
        self.store.save(self.incident, NOW)
        self.fixture = json.loads(FIXTURE.read_text())

    def test_fixture_is_versioned_and_ingests_then_reconnects(self):
        parsed = parse_producer_envelope(self.fixture, NOW)
        self.assertEqual(parsed.source, "aster-gateway-status/v1")
        self.store.ingest(self.fixture, NOW)
        reopened = IncidentStore(Path(self.tmp.name) / "incidents.sqlite3")
        snapshot = reopened.reconnect_snapshot("fixture-incident-001", NOW)
        self.assertEqual(snapshot["type"], "aster.incident")
        self.assertEqual(snapshot["incident"]["observations"][0]["age_seconds"], 120)
        self.assertEqual(snapshot["incident"]["next"]["target"], "inference-server")

    def test_envelope_rejects_unknown_fields_version_source_and_future_time(self):
        for mutate in (
            lambda value: value.update(extra=True),
            lambda value: value.update(schema_version=2),
            lambda value: value.update(producer="Bad producer"),
            lambda value: value.update(produced_at="2026-09-28T18:01:00Z"),
        ):
            value = json.loads(json.dumps(self.fixture))
            mutate(value)
            with self.assertRaises(InvestigationError):
                parse_producer_envelope(value, NOW)

    def test_tampered_persisted_record_fails_closed(self):
        with self.store._db() as db:
            db.execute("UPDATE incidents SET record=? WHERE incident_id=?", ("{}", "fixture-incident-001"))
        with self.assertRaises(InvestigationError):
            self.store.load("fixture-incident-001")

    def test_duplicate_delivery_never_duplicates_evidence(self):
        self.store.ingest(self.fixture, NOW)
        with self.assertRaises(InvestigationError):
            self.store.ingest(self.fixture, NOW)


if __name__ == "__main__":
    unittest.main()
