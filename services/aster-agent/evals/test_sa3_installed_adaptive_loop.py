import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sa3_installed_adaptive_loop import run
from sysadmin_investigation import Observation


NOW = datetime(2026, 10, 28, 20, 0, tzinfo=timezone.utc)


def doctor_reader(incident_id, path, now):
    return Observation(
        evidence_id="doctor-fixture", incident_id=incident_id,
        target="homelab-doctor", kind="status", observed_at=now.isoformat(),
        source="fixture-doctor/v1", state="ok", summary="Fixture Doctor report is healthy.",
        facts={"check_count": 1},
    )


def transport(request, key):
    remaining = request["remaining_checks"]
    disposition = "observe" if remaining else "complete"
    return {
        "schema_version": 1,
        "request_ref": request["request_ref"],
        "disposition": disposition,
        "hypothesis_summary": "The bounded fixture evidence supports the next registered step.",
        "target": remaining[0]["target"] if remaining else None,
        "kind": remaining[0]["kind"] if remaining else None,
        "evidence_refs": [item["evidence_ref"] for item in request["observations"]],
    }


def executor(store, incident_id, now):
    claim = store.pending_follow_up_claim(incident_id, now)
    target, kind = claim["target"], claim["kind"]
    envelope = {
        "schema_version": 1,
        "producer": "fixture-producer/v1",
        "produced_at": now.isoformat(),
        "observation": {
            "evidence_id": "fixture-" + target,
            "incident_id": incident_id,
            "target": target,
            "kind": kind,
            "observed_at": now.isoformat(),
            "state": "ok",
            "summary": "The registered fixture observation is healthy.",
            "facts": {"availability": "serving"},
            "truncated": False,
        },
    }
    return store.ingest(envelope, now, expected_decision_ref=claim["decision_ref"])


class InstalledAdaptiveLoopTests(unittest.TestCase):
    def test_three_stage_loop_completes_without_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "state"
            state.mkdir(mode=0o700)
            result = run(
                state, "fixture-key", now=NOW, doctor_reader=doctor_reader,
                transport=transport, executor=executor,
            )
        self.assertEqual("complete", result["status"])
        self.assertEqual("complete", result["terminal_disposition"])
        self.assertEqual(4, result["decision_count"])
        self.assertEqual(3, result["consumed_count"])
        self.assertEqual(
            ["homelab-doctor", "forgejo-main", "aster-gateway", "inference-server"],
            result["observation_targets"],
        )
        self.assertTrue(all(step["authority"] == "none" for step in result["steps"]))
        self.assertTrue(all(step["effect"] == "none" for step in result["steps"]))

    def test_rejects_non_private_state_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "state"
            state.mkdir(mode=0o755)
            with self.assertRaisesRegex(ValueError, "0700"):
                run(state, "fixture-key", now=NOW)


if __name__ == "__main__":
    unittest.main()
