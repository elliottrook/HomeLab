import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sysadmin_followup_selector import incident_state_digest
from sysadmin_incident_store import IncidentStore
from sysadmin_investigation import EvidenceRequest, InvestigationError, create_incident
from sysadmin_registered_producer import execute_registered_pending_observation


NOW = datetime(2026, 10, 27, 7, 0, tzinfo=timezone.utc)


class RegisteredIncidentProducerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = IncidentStore(Path(self.temporary.name) / "incidents.sqlite3")

    def create(self, target="aster-gateway", kind="status"):
        incident = create_incident(
            "incident-producer-001",
            "Registered producer fixture",
            [EvidenceRequest(target, kind, "Use one registered read-only source.")],
        )
        self.store.save(incident, NOW)
        return incident

    def bind(self, incident, *, target="aster-gateway", kind="status", disposition="observe"):
        self.store.bind_follow_up({
            "schema_version": 1,
            "incident_id": incident.incident_id,
            "state_digest": incident_state_digest(incident),
            "hypothesis_summary": "The fixed gateway status can discriminate availability.",
            "disposition": disposition,
            "target": target if disposition == "observe" else None,
            "kind": kind if disposition == "observe" else None,
        }, NOW)

    def test_exact_pending_gateway_status_is_consumed(self):
        incident = self.create()
        self.bind(incident)
        record = execute_registered_pending_observation(self.store, incident.incident_id, NOW)
        self.assertEqual("aster-gateway", record["target"])
        self.assertEqual("status", record["kind"])
        self.assertEqual("ok", record["state"])
        self.assertEqual(
            {"service": "aster-agent", "availability": "serving"}, record["facts"]
        )
        journal = self.store.followup_journal_snapshot(incident.incident_id, NOW)
        self.assertEqual(1, journal["decision_count"])
        self.assertEqual(1, journal["consumed_count"])
        self.assertIsNone(journal["pending"])

    def test_no_pending_and_terminal_decisions_are_denied(self):
        incident = self.create()
        with self.assertRaisesRegex(InvestigationError, "no pending observation"):
            execute_registered_pending_observation(self.store, incident.incident_id, NOW)
        self.bind(incident, disposition="escalate")
        with self.assertRaisesRegex(InvestigationError, "no pending observation"):
            execute_registered_pending_observation(self.store, incident.incident_id, NOW)

    def test_other_registered_target_has_no_implicit_producer(self):
        incident = self.create("inference-server", "status")
        self.bind(incident, target="inference-server", kind="status")
        with self.assertRaisesRegex(InvestigationError, "no registered producer"):
            execute_registered_pending_observation(self.store, incident.incident_id, NOW)
        journal = self.store.followup_journal_snapshot(incident.incident_id, NOW)
        self.assertEqual(0, journal["consumed_count"])
        self.assertEqual("inference-server", journal["pending"]["target"])

    def test_rejects_naive_clock_without_consuming_decision(self):
        incident = self.create()
        self.bind(incident)
        with self.assertRaises(InvestigationError):
            execute_registered_pending_observation(
                self.store, incident.incident_id, datetime(2026, 10, 27, 7, 0)
            )
        self.assertEqual(
            0, self.store.followup_journal_snapshot(incident.incident_id, NOW)["consumed_count"]
        )


if __name__ == "__main__":
    unittest.main()
