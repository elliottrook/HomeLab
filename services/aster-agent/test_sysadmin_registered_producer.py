import tempfile
import unittest
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from sysadmin_followup_selector import incident_state_digest
from sysadmin_incident_store import IncidentStore
from sysadmin_investigation import EvidenceRequest, InvestigationError, create_incident
from sysadmin_registered_producer import (
    _doctor_status_envelope,
    _forgejo_status_envelope,
    _gateway_config_envelope,
    _inference_status_envelope,
    _netbox_network_envelope,
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

    def test_exact_pending_doctor_status_reads_fixed_report_and_is_consumed(self):
        report = Path(self.temporary.name) / "latest.json"
        report.write_text(json.dumps({
            "schema": 1,
            "generated_at": "2026-10-27T06:58:00Z",
            "status": "warning",
            "checks": [{"name": "Fixture", "status": "warn", "summary": "Bounded warning."}],
        }))
        incident = self.create("homelab-doctor", "status")
        self.bind(incident, target="homelab-doctor", kind="status")
        with patch("sysadmin_registered_producer.DOCTOR_REPORT", report):
            record = execute_registered_pending_observation(self.store, incident.incident_id, NOW)
        self.assertEqual(("homelab-doctor", "status", "warn"), (
            record["target"], record["kind"], record["state"],
        ))
        self.assertEqual(1, record["facts"]["check_count"])
        self.assertEqual(24, len(record["facts"]["report_digest"]))
        self.assertNotIn("Bounded warning", json.dumps(record))
        journal = self.store.followup_journal_snapshot(incident.incident_id, NOW)
        self.assertEqual(1, journal["consumed_count"])
        self.assertIsNone(journal["pending"])

    def test_unavailable_doctor_report_is_bounded_evidence(self):
        report = Path(self.temporary.name) / "missing.json"
        envelope = _doctor_status_envelope("incident-doctor-001", NOW, report)
        self.assertEqual("homelab-doctor-report/v1", envelope["producer"])
        observation = envelope["observation"]
        self.assertEqual("unavailable", observation["state"])
        self.assertEqual({"reason": "unreadable"}, observation["facts"])

    def test_exact_pending_forgejo_git_uses_fixed_report_and_is_consumed(self):
        incident = self.create("forgejo-main", "git")
        self.bind(incident, target="forgejo-main", kind="git")
        fixture = {
            "schema_version": 1, "source": "forgejo", "generated_at": "2026-10-27T07:00:00Z",
            "instance": {"version": "fixture"},
            "repositories": [{
                "owner": "private", "name": "private", "visibility": "private",
                "archived": False, "default_branch": "main", "updated_at": "2026-10-27T07:00:00Z",
                "counts": {"branches": 1, "tags": 0, "releases": 0, "open_issues": 0, "open_pulls": 0},
                "latest_commit": None, "latest_action": None,
            }],
        }
        with patch("forgejo_incident_adapter.get_forgejo_report", return_value=fixture), \
                patch("sysadmin_registered_producer.read_forgejo_observation") as reader:
            from forgejo_incident_adapter import read_forgejo_observation
            reader.side_effect = lambda incident_id, path, now: read_forgejo_observation(
                incident_id, path, now, reader=lambda path, now: fixture
            )
            record = execute_registered_pending_observation(self.store, incident.incident_id, NOW)
        self.assertEqual(("forgejo-main", "git", "ok"), (
            record["target"], record["kind"], record["state"],
        ))
        self.assertEqual(1, record["facts"]["repository_count"])
        self.assertEqual(1, self.store.followup_journal_snapshot(
            incident.incident_id, NOW
        )["consumed_count"])

    def test_exact_pending_netbox_network_uses_fixed_report_and_is_consumed(self):
        incident = self.create("netbox-main", "network")
        self.bind(incident, target="netbox-main", kind="network")
        fixture = {
            "schema_version": 1, "source": "netbox", "generated_at": "2026-10-27T07:00:00Z",
            "instance": {"version": "fixture"},
            "inventory": {
                "counts": {"devices": 2, "virtual_machines": 3, "sites": 1, "racks": 1, "vlans": 4, "prefixes": 5},
                "devices": [], "virtual_machines": [], "vlans": [], "prefixes": [],
            },
        }
        with patch("sysadmin_registered_producer.read_netbox_observation") as reader:
            from netbox_incident_adapter import read_netbox_observation
            reader.side_effect = lambda incident_id, path, now: read_netbox_observation(
                incident_id, path, now, reader=lambda path, now: fixture
            )
            record = execute_registered_pending_observation(self.store, incident.incident_id, NOW)
        self.assertEqual(("netbox-main", "network", "ok"), (
            record["target"], record["kind"], record["state"],
        ))
        self.assertEqual(2, record["facts"]["device_count"])
        self.assertEqual(1, self.store.followup_journal_snapshot(
            incident.incident_id, NOW
        )["consumed_count"])

    def test_unavailable_netbox_report_is_bounded_evidence(self):
        envelope = _netbox_network_envelope(
            "incident-netbox-001", NOW, Path(self.temporary.name) / "missing.json"
        )
        self.assertEqual("netbox-main-report/v1", envelope["producer"])
        self.assertEqual("unavailable", envelope["observation"]["state"])
        self.assertEqual({"reason": "source_unavailable"}, envelope["observation"]["facts"])

    def test_exact_pending_gateway_config_uses_fixed_identity_and_is_consumed(self):
        incident = self.create("aster-gateway", "config")
        self.bind(incident, target="aster-gateway", kind="config")
        with patch("sysadmin_registered_producer.read_gateway_config_observation") as reader:
            from sysadmin_investigation import Observation
            reader.return_value = Observation(
                evidence_id="gateway-config-" + "a" * 24,
                incident_id=incident.incident_id,
                target="aster-gateway",
                kind="config",
                observed_at=NOW.isoformat(),
                source="aster-gateway-config-identity/v1",
                state="ok",
                summary="Registered Aster gateway configuration identity is available.",
                facts={"service": "aster-agent", "file_count": 2, "configuration_digest": "a" * 24},
            )
            record = execute_registered_pending_observation(self.store, incident.incident_id, NOW)
        self.assertEqual(("aster-gateway", "config", "ok"), (
            record["target"], record["kind"], record["state"],
        ))
        self.assertEqual(2, record["facts"]["file_count"])
        self.assertEqual(1, self.store.followup_journal_snapshot(
            incident.incident_id, NOW
        )["consumed_count"])

    def test_unavailable_gateway_config_is_bounded_evidence(self):
        with patch("sysadmin_registered_producer.read_gateway_config_observation") as reader:
            from sysadmin_investigation import Observation
            reader.return_value = Observation(
                evidence_id="gateway-config-unavailable-" + "b" * 24,
                incident_id="incident-config-001",
                target="aster-gateway",
                kind="config",
                observed_at=NOW.isoformat(),
                source="aster-gateway-config-identity/v1",
                state="unavailable",
                summary="Registered Aster gateway configuration identity is unavailable.",
                facts={"reason": "source_unavailable"},
            )
            envelope = _gateway_config_envelope("incident-config-001", NOW)
        self.assertEqual("aster-gateway-config-identity/v1", envelope["producer"])
        self.assertEqual("unavailable", envelope["observation"]["state"])
        self.assertEqual({"reason": "source_unavailable"}, envelope["observation"]["facts"])

    def test_changed_pending_decision_cannot_be_consumed_by_stale_result(self):
        incident = create_incident(
            "incident-producer-race",
            "Registered producer race fixture",
            [
                EvidenceRequest("aster-gateway", "status", "First fixed observation."),
                EvidenceRequest("aster-gateway", "status", "Second fixed observation."),
            ],
        )
        self.store.save(incident, NOW)
        self.bind(incident)
        from sysadmin_registered_producer import _gateway_status_envelope as real_gateway_envelope

        def replace_pending(incident_id, now):
            first = self.store.pending_follow_up_claim(incident_id, now)
            envelope = {
                "schema_version": 1,
                "producer": "aster-gateway-self-status/v1",
                "produced_at": "2026-10-27T07:00:00Z",
                "observation": {
                    "evidence_id": "race-first",
                    "incident_id": incident_id,
                    "target": "aster-gateway",
                    "kind": "status",
                    "observed_at": "2026-10-27T07:00:00Z",
                    "state": "ok",
                    "summary": "First result.",
                    "facts": {},
                    "truncated": False,
                },
            }
            self.store.ingest(envelope, now, expected_decision_ref=first["decision_ref"])
            current = self.store.load(incident_id, now)
            self.bind(current)
            return real_gateway_envelope(incident_id, now)

        with patch("sysadmin_registered_producer._gateway_status_envelope", side_effect=replace_pending):
            with self.assertRaisesRegex(InvestigationError, "changed"):
                execute_registered_pending_observation(self.store, incident.incident_id, NOW)
        journal = self.store.followup_journal_snapshot(incident.incident_id, NOW)
        self.assertEqual(2, journal["decision_count"])
        self.assertEqual(1, journal["consumed_count"])
        self.assertEqual("status", journal["pending"]["kind"])


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
