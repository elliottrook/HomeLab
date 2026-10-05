import unittest
from datetime import datetime, timedelta, timezone

from sysadmin_investigation import (
    EvidenceRequest,
    InvestigationError,
    Observation,
    create_incident,
)


NOW = datetime(2026, 9, 28, 18, 0, tzinfo=timezone.utc)


def observation(**changes):
    data = {
        "evidence_id": "obs-001", "incident_id": "inc-001", "target": "aster-gateway",
        "kind": "status", "observed_at": "2026-09-28T17:58:00Z",
        "source": "aster-agent-status-adapter/v1", "state": "warn",
        "summary": "Gateway response budget was reached.", "facts": {"response_cap": 500},
    }
    data.update(changes)
    return Observation(**data)


class InvestigationTests(unittest.TestCase):
    def incident(self):
        return create_incident("inc-001", "Gateway diagnosis", [
            EvidenceRequest("aster-gateway", "status", "Establish current gateway state."),
            EvidenceRequest("inference-server", "status", "Check the bounded inference dependency."),
        ])

    def test_records_provenance_age_and_next_read_only_step(self):
        incident = self.incident()
        incident.add_hypothesis("A response cap may be limiting the answer.")
        record = incident.add_observation(observation(), NOW)
        self.assertEqual(record["age_seconds"], 120)
        self.assertEqual(record["source"], "aster-agent-status-adapter/v1")
        self.assertFalse(record["truncated"])
        self.assertEqual(incident.next_observation()["target"], "inference-server")
        self.assertEqual(incident.next_observation()["execution"], "not performed by the investigation loop")

    def test_rejects_unregistered_future_secret_and_cross_incident_evidence(self):
        incident = self.incident()
        with self.assertRaises(InvestigationError):
            incident.add_observation(observation(target="opnsense", kind="config"), NOW)
        with self.assertRaises(InvestigationError):
            incident.add_observation(observation(observed_at="2026-09-28T18:01:00Z"), NOW)
        with self.assertRaises(InvestigationError):
            incident.add_observation(observation(facts={"token": "no"}), NOW)
        with self.assertRaises(InvestigationError):
            incident.add_observation(observation(facts={"safe": {"credential_hint": "no"}}), NOW)
        with self.assertRaises(InvestigationError):
            incident.add_observation(observation(incident_id="inc-other"), NOW)

    def test_preserves_unavailable_and_truncated_evidence_without_claiming_completion(self):
        incident = self.incident()
        incident.add_observation(observation(state="unavailable", truncated=True, facts={"error_class": "timeout"}), NOW)
        state = incident.public_state()
        self.assertEqual(state["observations"][0]["state"], "unavailable")
        self.assertTrue(state["observations"][0]["truncated"])
        self.assertEqual(state["next"]["state"], "proposed_read_only")

    def test_plan_and_hypothesis_bounds_fail_closed(self):
        with self.assertRaises(InvestigationError):
            create_incident("a", "b", [EvidenceRequest("forgejo-main", "git", "x")] * 5)
        incident = self.incident()
        for i in range(3):
            incident.add_hypothesis(f"hypothesis {i}")
        with self.assertRaises(InvestigationError):
            incident.add_hypothesis("one too many")
        for i in range(4):
            incident.add_observation(observation(evidence_id=f"obs-{i}", observed_at=(NOW - timedelta(seconds=i)).isoformat().replace("+00:00", "Z")), NOW)
        self.assertEqual(incident.next_observation()["state"], "bounded")

    def test_catalogue_covers_each_approved_read_only_evidence_kind(self):
        plan = [
            EvidenceRequest("forgejo-main", "git", "Source revision."),
            EvidenceRequest("aster-gateway", "log", "Bounded service event."),
            EvidenceRequest("aster-gateway", "status", "Current status."),
            EvidenceRequest("homelab-doctor", "network", "Sanitized reachability."),
        ]
        # A plan is intentionally short; the catalogue separately enables
        # backup and config evidence for cases whose initial observations call
        # for them.
        self.assertEqual(len(create_incident("inc-catalogue", "Catalogue", plan).observation_plan), 4)
        self.assertEqual(EvidenceRequest("backup-catalog", "backup", "Coverage.").kind, "backup")
        self.assertEqual(EvidenceRequest("inference-server", "config", "Pinned runtime.").kind, "config")


if __name__ == "__main__":
    unittest.main()
