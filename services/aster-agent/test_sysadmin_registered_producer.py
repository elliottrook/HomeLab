import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sysadmin_followup_selector import incident_state_digest
from sysadmin_incident_store import IncidentStore
from sysadmin_investigation import EvidenceRequest, InvestigationError, create_incident
from sysadmin_registered_producer import (
    _inference_status_envelope,
    execute_registered_pending_observation,
)


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

    def test_registered_pair_without_a_producer_remains_pending(self):
        incident = self.create("aster-gateway", "log")
        self.bind(incident, target="aster-gateway", kind="log")
        with self.assertRaisesRegex(InvestigationError, "no registered producer"):
            execute_registered_pending_observation(self.store, incident.incident_id, NOW)
        journal = self.store.followup_journal_snapshot(incident.incident_id, NOW)
        self.assertEqual(0, journal["consumed_count"])
        self.assertEqual("log", journal["pending"]["kind"])

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


class FakeResponse:
    def __init__(self, status=200, body=b'{"status":"ok"}'):
        self.status = status
        self.body = body

    def read(self, limit):
        return self.body[:limit]


class FakeConnection:
    def __init__(self, host, port, timeout, *, response=None, error=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.response = response or FakeResponse()
        self.error = error
        self.request_value = None
        self.closed = False

    def request(self, method, path, headers):
        self.request_value = (method, path, headers)
        if self.error:
            raise self.error

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


class InferenceHealthProducerTests(unittest.TestCase):
    def envelope(self, *, response=None, error=None):
        connections = []

        def factory(host, port, timeout):
            connection = FakeConnection(host, port, timeout, response=response, error=error)
            connections.append(connection)
            return connection

        envelope = _inference_status_envelope("incident-inference-001", NOW, factory)
        return envelope, connections[0]

    def test_exact_fixed_health_request_maps_to_bounded_ok(self):
        envelope, connection = self.envelope()
        self.assertEqual(("192.168.70.12", 11435, 3), (connection.host, connection.port, connection.timeout))
        self.assertEqual(("GET", "/health", {"Accept": "application/json"}), connection.request_value)
        self.assertTrue(connection.closed)
        observation = envelope["observation"]
        self.assertEqual("inference-server", observation["target"])
        self.assertEqual("status", observation["kind"])
        self.assertEqual("ok", observation["state"])
        self.assertEqual({"service": "aster-llama", "endpoint": "health"}, observation["facts"])

    def test_failure_wrong_status_shape_duplicate_and_oversize_abstain(self):
        cases = (
            {"error": OSError("fixture")},
            {"response": FakeResponse(status=503)},
            {"response": FakeResponse(body=b'{"status":"warming"}')},
            {"response": FakeResponse(body=b'{"status":"ok","status":"ok"}')},
            {"response": FakeResponse(body=b"x" * 1025)},
        )
        for values in cases:
            with self.subTest(values=values):
                envelope, connection = self.envelope(**values)
                self.assertTrue(connection.closed)
                observation = envelope["observation"]
                self.assertEqual("unavailable", observation["state"])
                self.assertEqual({}, observation["facts"])


if __name__ == "__main__":
    unittest.main()
