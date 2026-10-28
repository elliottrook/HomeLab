import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from sa3_installed_gateway_smoke import run


NOW = datetime(2026, 10, 28, 18, 0, tzinfo=timezone.utc)


class InstalledGatewaySmokeTests(unittest.TestCase):
    def test_one_no_effect_decision_is_journaled(self):
        def transport(request, api_key):
            self.assertEqual("fixture-key", api_key)
            return {
                "schema_version": 1,
                "request_ref": request["request_ref"],
                "disposition": "observe",
                "hypothesis_summary": "Inference status is the next bounded check.",
                "target": "inference-server",
                "kind": "status",
                "evidence_refs": [item["evidence_ref"] for item in request["observations"]],
            }

        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "state"
            state.mkdir(mode=0o700)
            with patch("sa3_installed_gateway_smoke.propose_and_bind_follow_up") as gateway:
                from sysadmin_proposal_gateway import propose_and_bind_follow_up
                gateway.side_effect = lambda store, incident_id, key, now: propose_and_bind_follow_up(
                    store, incident_id, key, transport=transport, now=now
                )
                result = run(state, "fixture-key", NOW)
        self.assertEqual("complete", result["status"])
        self.assertEqual(1, result["decision_count"])
        self.assertEqual(0, result["consumed_count"])
        self.assertEqual("observe", result["disposition"])
        self.assertEqual("inference-server", result["target"])
        self.assertEqual("status", result["kind"])
        self.assertEqual("none", result["authority"])
        self.assertEqual("none", result["effect"])
        self.assertEqual(1, result["observation_count"])

    def test_rejects_non_private_state_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "state"
            state.mkdir(mode=0o755)
            with self.assertRaisesRegex(ValueError, "0700"):
                run(state, "fixture-key", NOW)


if __name__ == "__main__":
    unittest.main()
