import json
import os
import sqlite3
import stat
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sysadmin_incident_store import IncidentStore, parse_producer_envelope
from sysadmin_followup_selector import incident_state_digest
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
            lambda value: value.update(schema_version=True),
            lambda value: value.update(producer="Bad producer"),
            lambda value: value.update(produced_at="2026-09-28T18:01:00Z"),
        ):
            value = json.loads(json.dumps(self.fixture))
            mutate(value)
            with self.assertRaises(InvestigationError):
                parse_producer_envelope(value, NOW)

    def test_malformed_producer_types_fail_with_contract_error(self):
        for field, invalid in (
            ("evidence_id", 7), ("incident_id", 7), ("target", []),
            ("kind", []), ("state", {}), ("facts", {"latency": float("nan")}),
        ):
            value = json.loads(json.dumps(self.fixture))
            value["observation"][field] = invalid
            with self.subTest(field=field), self.assertRaises(InvestigationError):
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

    def test_retention_prunes_expired_incidents_before_new_write_or_reconnect(self):
        later = NOW + timedelta(hours=24, seconds=1)
        replacement = create_incident("fixture-incident-002", "Replacement", [
            EvidenceRequest("homelab-doctor", "status", "Read the sanitized report."),
        ])
        self.store.save(replacement, later)
        with self.assertRaises(InvestigationError):
            self.store.load("fixture-incident-001", later)
        self.assertEqual(self.store.load("fixture-incident-002", later).title, "Replacement")

    def test_count_and_storage_limits_fail_closed(self):
        store = IncidentStore(Path(self.tmp.name) / "limited.sqlite3", max_incidents=1)
        first = create_incident("limited-1", "First", [EvidenceRequest("homelab-doctor", "status", "Read report.")])
        second = create_incident("limited-2", "Second", [EvidenceRequest("homelab-doctor", "status", "Read report.")])
        store.save(first, NOW)
        with self.assertRaises(InvestigationError):
            store.save(second, NOW)
        tiny = IncidentStore(Path(self.tmp.name) / "tiny.sqlite3", max_database_bytes=16_384)
        with self.assertRaises(InvestigationError):
            tiny.save(first, NOW)

    def test_database_and_directory_require_private_custody(self):
        path = Path(self.tmp.name) / "incidents.sqlite3"
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        os.chmod(path, 0o644)
        with self.assertRaisesRegex(InvestigationError, "database custody"):
            self.store.load("fixture-incident-001", NOW)
        os.chmod(path, 0o600)
        os.chmod(path.parent, 0o755)
        with self.assertRaisesRegex(InvestigationError, "directory custody"):
            self.store.load("fixture-incident-001", NOW)

    def test_symlinked_database_is_rejected_before_sqlite_connect(self):
        target = Path(self.tmp.name) / "incidents.sqlite3"
        link = Path(self.tmp.name) / "alias.sqlite3"
        link.symlink_to(target)
        with self.assertRaisesRegex(InvestigationError, "database custody"):
            IncidentStore(link)

    def test_database_context_closes_connection(self):
        with self.store._db() as db:
            self.assertEqual(db.execute("SELECT 1").fetchone()[0], 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            db.execute("SELECT 1")

    def followup(self, **changes):
        proposal = {
            "schema_version": 1,
            "incident_id": self.incident.incident_id,
            "state_digest": incident_state_digest(self.store.load(self.incident.incident_id, NOW)),
            "hypothesis_summary": "The dependency state should discriminate the failure.",
            "disposition": "observe",
            "target": "aster-gateway",
            "kind": "status",
        }
        proposal.update(changes)
        return proposal

    def test_bound_followup_survives_reconnect_and_matching_ingest_consumes_it(self):
        decision = self.store.bind_follow_up(self.followup(), NOW)
        reopened = IncidentStore(Path(self.tmp.name) / "incidents.sqlite3")
        self.assertEqual(reopened.pending_follow_up(self.incident.incident_id, NOW), decision)
        reopened.ingest(self.fixture, NOW)
        self.assertIsNone(reopened.pending_follow_up(self.incident.incident_id, NOW))
        with reopened._db() as db:
            row = db.execute(
                "SELECT consumed_at FROM followup_decisions WHERE incident_id=?",
                (self.incident.incident_id,),
            ).fetchone()
        self.assertIsNotNone(row["consumed_at"])

    def test_pending_followup_blocks_second_decision_and_mismatched_result(self):
        self.store.bind_follow_up(self.followup(), NOW)
        with self.assertRaisesRegex(InvestigationError, "pending follow-up"):
            self.store.bind_follow_up(self.followup(), NOW)
        mismatched = json.loads(json.dumps(self.fixture))
        mismatched["producer"] = "inference-server-status/v1"
        mismatched["observation"].update(
            target="inference-server",
            evidence_id="evidence-inference-status",
        )
        with self.assertRaisesRegex(InvestigationError, "does not match pending"):
            self.store.ingest(mismatched, NOW)
        self.assertIsNotNone(self.store.pending_follow_up(self.incident.incident_id, NOW))

    def test_changed_incident_state_makes_pending_decision_stale(self):
        self.store.bind_follow_up(self.followup(), NOW)
        changed = self.store.load(self.incident.incident_id, NOW)
        changed.add_hypothesis("A separately persisted revision.")
        self.store.save(changed, NOW)
        with self.assertRaisesRegex(InvestigationError, "stale persisted"):
            self.store.pending_follow_up(self.incident.incident_id, NOW)


if __name__ == "__main__":
    unittest.main()
