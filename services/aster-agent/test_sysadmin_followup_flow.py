import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sysadmin_followup_selector import incident_state_digest
from sysadmin_incident_store import IncidentStore
from sysadmin_investigation import EvidenceRequest, create_incident


NOW = datetime(2026, 10, 27, 6, 15, tzinfo=timezone.utc)


class FollowUpFlowTests(unittest.TestCase):
    def test_two_adaptive_checks_and_terminal_escalation_survive_reconnects(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "incidents.sqlite3"
            store = IncidentStore(path)
            incident = create_incident(
                "incident-multistep-001",
                "Gateway is available but answers are incomplete",
                [
                    EvidenceRequest("aster-gateway", "status", "Confirm gateway state."),
                    EvidenceRequest("inference-server", "status", "Check the inference dependency."),
                    EvidenceRequest("aster-gateway", "log", "Inspect bounded gateway errors."),
                ],
            )
            store.save(incident, NOW)

            first = {
                "schema_version": 1,
                "incident_id": incident.incident_id,
                "state_digest": incident_state_digest(incident),
                "hypothesis_summary": "A gateway error may discriminate the incomplete answer.",
                "disposition": "observe",
                "target": "aster-gateway",
                "kind": "log",
            }
            store.bind_follow_up(first, NOW)
            store = IncidentStore(path)
            self.assertEqual(store.pending_follow_up(incident.incident_id, NOW)["request"]["kind"], "log")
            store.ingest({
                "schema_version": 1,
                "producer": "aster-gateway-log/v1",
                "produced_at": "2026-10-27T06:14:30Z",
                "observation": {
                    "evidence_id": "gateway-log-001",
                    "incident_id": incident.incident_id,
                    "target": "aster-gateway",
                    "kind": "log",
                    "observed_at": "2026-10-27T06:14:00Z",
                    "state": "warn",
                    "summary": "The bounded log view shows a dependency warning.",
                    "facts": {"warning_count": 1},
                    "truncated": False,
                },
            }, NOW)

            store = IncidentStore(path)
            current = store.load(incident.incident_id, NOW)
            second = dict(first)
            second.update(
                state_digest=incident_state_digest(current),
                hypothesis_summary="The dependency warning now makes backend status discriminating.",
                target="inference-server",
                kind="status",
            )
            store.bind_follow_up(second, NOW)
            store.ingest({
                "schema_version": 1,
                "producer": "inference-server-status/v1",
                "produced_at": "2026-10-27T06:14:50Z",
                "observation": {
                    "evidence_id": "inference-status-001",
                    "incident_id": incident.incident_id,
                    "target": "inference-server",
                    "kind": "status",
                    "observed_at": "2026-10-27T06:14:45Z",
                    "state": "unavailable",
                    "summary": "The registered status source was unavailable.",
                    "facts": {"available": False},
                    "truncated": False,
                },
            }, NOW)

            store = IncidentStore(path)
            current = store.load(incident.incident_id, NOW)
            terminal = dict(first)
            terminal.update(
                state_digest=incident_state_digest(current),
                hypothesis_summary="The unavailable dependency evidence prevents a safe diagnosis.",
                disposition="escalate",
                target=None,
                kind=None,
            )
            store.bind_follow_up(terminal, NOW)
            store = IncidentStore(path)
            pending = store.pending_follow_up(incident.incident_id, NOW)
            self.assertEqual(pending["disposition"], "escalate")
            self.assertIsNone(pending["request"])
            self.assertEqual(store.reconnect_snapshot(incident.incident_id, NOW)["incident"]["observation_count"], 2)
            with store._db() as db:
                rows = db.execute(
                    "SELECT consumed_at FROM followup_decisions WHERE incident_id=? ORDER BY decision_id",
                    (incident.incident_id,),
                ).fetchall()
            self.assertEqual(3, len(rows))
            self.assertTrue(all(row["consumed_at"] is not None for row in rows[:2]))
            self.assertIsNone(rows[2]["consumed_at"])


if __name__ == "__main__":
    unittest.main()
