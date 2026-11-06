import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sa4_one_shot_transaction_controller_v2 as controller
import sa4_one_use_grant_ledger_v1 as ledger_module
import sa4_root_transaction_owner_v2 as owner_module


EPOCHS = {
    "measurement": 100, "checkpoint": 101, "claim": 102,
    "claim_deadline": 180, "effect": 103, "observation": 104,
    "rollback": 105, "rollback_observation": 106, "finish": 107,
}
PACKET = {name: f"{name}\n".encode() for name in (
    "plan", "approval", "approval_proof", "grant", "grant_proof")}


class FakeOwner:
    operation_id = "sa4-v4-operation"

    def __init__(self, branch="ready-to-reconcile"):
        self.phase = "new"; self.branch = branch; self.calls = []

    def prepare(self, *args, **kwargs):
        self.calls.append("prepare")
        return {"measurement": b"measurement\n", "checkpoint": b"checkpoint\n"}
    def execute_once(self, **kwargs):
        self.calls.append("execute")
        return {name: f"{name}\n".encode() for name in
                ("source", "claim", "admission", "terminal")}
    def observe(self, **kwargs):
        self.calls.append("observe"); return b"postcheck\n"
    def accept_postcheck_proof(self, raw):
        self.calls.append("accept-postcheck"); return self.branch
    def rollback_once(self, **kwargs):
        self.calls.append("rollback"); return b"rollback\n"
    def retained_evidence(self, name): return f"{name}\n".encode()
    def accept_rollback_proof(self, raw): self.calls.append("accept-rollback")
    def finish(self, **kwargs):
        self.calls.append("finish"); self.phase = "terminal"
        return {"state": "burned"}


class SA4OneShotTransactionControllerTests(unittest.TestCase):
    def owner(self, branch="ready-to-reconcile"):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        ledger = ledger_module.OneUseLedger(Path(temporary.name) / "ledger")
        value = FakeOwner(branch)
        value.__class__ = type("AcceptedFakeOwner", (
            FakeOwner, owner_module.RootTransactionOwner), {})
        return value

    def invoke(self, branch="ready-to-reconcile"):
        owner = self.owner(branch)
        signatures = []
        evidence = []
        def signer(statement):
            signatures.append(statement); return "a" * 512
        def writer(name, raw): evidence.append((name, raw))
        with patch.object(controller.observer, "validate_statement",
                          side_effect=lambda raw: raw):
            result = controller.run(
                owner, PACKET, b"candidate\n", EPOCHS,
                observer_signer=signer, evidence_writer=writer)
        return owner, signatures, evidence, result

    def test_success_is_one_effect_path_and_one_observer_signature(self):
        owner, signatures, evidence, result = self.invoke()
        self.assertEqual(["prepare", "execute", "observe",
                          "accept-postcheck", "finish"], owner.calls)
        self.assertEqual(1, len(signatures))
        self.assertEqual("reconciliation", evidence[-1][0])
        self.assertEqual("postcheck-complete", result["branch"])
        self.assertFalse(result["automatic_retry"])

    def test_failed_postcheck_rolls_back_once_and_signs_twice(self):
        owner, signatures, evidence, result = self.invoke("rollback-required")
        self.assertEqual(["prepare", "execute", "observe",
                          "accept-postcheck", "rollback", "accept-rollback",
                          "finish"], owner.calls)
        self.assertEqual(2, len(signatures))
        self.assertIn(("rollback_terminal", b"rollback_terminal\n"), evidence)
        self.assertEqual("rollback", result["branch"])

    def test_observer_failure_stops_without_finish_or_retry(self):
        owner = self.owner()
        with patch.object(controller.observer, "validate_statement",
                          side_effect=lambda raw: raw), self.assertRaises(ValueError):
            controller.run(owner, PACKET, b"candidate\n", EPOCHS,
                           observer_signer=lambda _raw: "bad",
                           evidence_writer=lambda _name, _raw: None)
        self.assertEqual(["prepare", "execute", "observe"], owner.calls)
        self.assertNotIn("finish", owner.calls)

    def test_input_drift_fails_before_owner_call(self):
        owner = self.owner()
        changed = dict(EPOCHS); changed.pop("finish")
        with self.assertRaises(ValueError):
            controller.run(owner, PACKET, b"candidate\n", changed,
                           observer_signer=lambda _raw: "a" * 512,
                           evidence_writer=lambda _name, _raw: None)
        self.assertEqual([], owner.calls)


if __name__ == "__main__":
    unittest.main()
