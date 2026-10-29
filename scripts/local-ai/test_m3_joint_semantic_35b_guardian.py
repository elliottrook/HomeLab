from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import m3_joint_semantic_35b_guardian as guardian


class GuardianTests(unittest.TestCase):
    def test_absent_state_is_no_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            value = guardian.run(owner_id="aster-local-ai-pilot-owner-x",
                owner_unit="aster-local-ai-pilot-owner-x.scope", cycle="2026_10_29",
                rescue_at=10, hard_deadline=910, state_path=Path(tmp)/"absent",
                clock=lambda: 10, sleep=lambda _: None)
        self.assertEqual("not-attempted", value["effects"])

    def test_exact_state_is_fenced_then_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"state.json"
            owner = "lh-12345678"
            path.write_text(json.dumps({"owner_id": owner,
                "mode": "full-inference-drain-v1", "phase": "drained",
                "lease_id": owner+":123", "generation": 1}))
            seen = []
            def recovered(value):
                seen.append(value); path.unlink()
            value = guardian.run(owner_id=owner, owner_unit=owner+".scope",
                cycle="2026_10_29", rescue_at=10, hard_deadline=910,
                state_path=path, clock=lambda: 10, sleep=lambda _: None,
                fence=lambda unit,budget: True, recoverer=recovered)
        self.assertEqual("restored", value["effects"])
        self.assertEqual(1, len(seen))

    def test_foreign_owner_fails_closed(self):
        with self.assertRaises(guardian.GuardianError):
            guardian.identity({"owner_id":"foreign","mode":"full-inference-drain-v1",
                "phase":"drained","lease_id":"foreign:1","generation":1},
                owner_id="aster-local-ai-pilot-owner-x", cycle="2026_10_29")


if __name__ == "__main__":
    unittest.main()

