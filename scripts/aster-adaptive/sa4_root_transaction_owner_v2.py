"""Single fail-closed coordinator for one supervised SA4 transaction.

The coordinator has no command runner, signer, transport, retry path or live
host binding.  It sequences the fixed owners and deliberately pauses for the
independent observer proof after each observation.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import re

import sa4_atomic_repair_owner_v1 as repair_owner
import sa4_atomic_rollback_owner_v1 as rollback_owner
import sa4_authenticated_authority_v1 as authority
import sa4_effect_admission_v1 as effect_admission
import sa4_inactive_checkpoint_owner_v1 as checkpoint_owner
import sa4_inactive_measurement_owner_v1 as measurement_owner
import sa4_independent_postcheck_receipt_v1 as receipt_validator
import sa4_independent_receipt_producer_v1 as receipt_producer
import sa4_independent_rollback_receipt_producer_v1 as rollback_producer
import sa4_one_use_grant_ledger_v1 as ledger_module
import sa4_preflight_composition_v1 as preflight
import sa4_receipt_ledger_reconciler_v2 as reconciler
import sa4_runtime_control_owner_v1 as runtime_owner
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry


IDENTITY = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
BOUND_HOST_ID = "lxc104"


@contextmanager
def _fixed_bindings(plan_raw: bytes):
    plan = contract.validate_plan(plan_raw)
    target = registry.resolve_production(plan["target_id"])
    modules = (runtime_owner, measurement_owner, checkpoint_owner,
               repair_owner, receipt_producer, rollback_owner,
               rollback_producer)
    originals = tuple(module.LOCAL_HOST_ID for module in modules)
    if (target.host_id != BOUND_HOST_ID
            or any(value not in {"unconfigured", BOUND_HOST_ID}
                   for value in originals)):
        raise ValueError("SA4 root-owner fixed host binding changed")
    for module in modules: module.LOCAL_HOST_ID = BOUND_HOST_ID
    try:
        yield
    finally:
        for module, original in zip(modules, originals):
            module.LOCAL_HOST_ID = original


def _raw(value: object) -> bytes:
    return contract.canonical(value)


class RootTransactionOwner:
    """Own exactly one in-memory transaction with a closed phase graph."""

    def __init__(self, ledger: object, *, operation_id: str):
        if (not isinstance(ledger, ledger_module.OneUseLedger)
                or not IDENTITY.fullmatch(operation_id)):
            raise ValueError("SA4 root transaction identity changed")
        self.ledger = ledger
        self.operation_id = operation_id
        self.phase = "new"
        self._values: dict[str, bytes] = {}
        self.controls: runtime_owner.RuntimeControlOwner | None = None

    def _require(self, phase: str) -> None:
        if self.phase != phase:
            raise ValueError("SA4 root transaction phase changed")

    def prepare(self, plan_raw: bytes, approval_raw: bytes,
                approval_proof_raw: bytes, grant_raw: bytes,
                grant_proof_raw: bytes, candidate_raw: bytes, *,
                measurement_epoch: int,
                checkpoint_epoch: int) -> dict[str, bytes]:
        """Measure and checkpoint once; still authorize no repair effect."""
        self._require("new")
        self.phase = "preparation-in-progress"
        try:
            plan = contract.validate_plan(plan_raw)
            if (hashlib.sha256(candidate_raw).hexdigest()
                    != plan["change"]["artifact_sha256"]):
                raise ValueError("SA4 candidate does not match the fixed plan")
            authority.verify(
                plan_raw, approval_raw, approval_proof_raw, grant_raw,
                grant_proof_raw, checkpoint_epoch)
            with _fixed_bindings(plan_raw):
                self.controls = runtime_owner.RuntimeControlOwner(plan_raw)
                self.controls.acquire()
                measurement_raw = _raw(measurement_owner.measure(
                    plan_raw, measurement_epoch=measurement_epoch))
                checkpoint_raw = _raw(checkpoint_owner.create(
                    plan_raw, measurement_raw, checkpoint_epoch=checkpoint_epoch))
        except BaseException:
            if self.controls is not None:
                self.controls.retain_uncertain()
            self.phase = "uncertain-manual-reconciliation-required"
            raise
        self._values = {
            "plan": plan_raw, "approval": approval_raw,
            "approval_proof": approval_proof_raw, "grant": grant_raw,
            "grant_proof": grant_proof_raw, "candidate": candidate_raw,
            "measurement": measurement_raw, "checkpoint": checkpoint_raw}
        self.phase = "prepared"
        return {name: self._values[name] for name in
                ("measurement", "checkpoint")}

    def execute_once(self, *, claim_epoch: int, claim_deadline_epoch: int,
                     effect_epoch: int) -> dict[str, bytes]:
        """Claim once, emit final admission and attempt exactly one repair."""
        self._require("prepared")
        self.phase = "effect-in-progress"
        try:
            if self.controls is None:
                raise ValueError("SA4 runtime controls are absent")
            runtime_controls_raw = self.controls.observe(effect_epoch)
            source_raw = _raw(preflight.compose_live(
                self._values["plan"], self._values["approval"],
                self._values["approval_proof"], self._values["grant"],
                self._values["grant_proof"], self._values["measurement"],
                self._values["checkpoint"], runtime_controls_raw,
                self.ledger, effect_epoch))
            source = contract.decode_unique_json(source_raw)
            claim = self.ledger.claim(
                source["grant_id"], claimant=self.operation_id,
                now_epoch=claim_epoch, deadline_epoch=claim_deadline_epoch)
            claim_raw = _raw(claim)
            admission_raw = effect_admission.admit(
                self._values["plan"], self._values["approval"],
                self._values["approval_proof"], self._values["grant"],
                self._values["grant_proof"], source_raw,
                self._values["checkpoint"], claim_raw,
                self._values["candidate"], effect_epoch=effect_epoch)
            with _fixed_bindings(self._values["plan"]):
                terminal_raw = _raw(repair_owner.execute(
                    self._values["plan"], admission_raw,
                    self._values["checkpoint"], claim_raw,
                    self._values["candidate"], operation_id=self.operation_id,
                    effect_epoch=effect_epoch))
        except BaseException:
            if self.controls is not None:
                self.controls.retain_uncertain()
            self.phase = "uncertain-manual-reconciliation-required"
            raise
        self._values.update(source=source_raw, claim=claim_raw,
                            admission=admission_raw, terminal=terminal_raw)
        self.phase = "effect-attempted"
        return {name: self._values[name]
                for name in ("source", "claim", "admission", "terminal")}

    def observe(self, *, observed_epoch: int) -> bytes:
        """Produce the unsigned independent receipt and pause for signing."""
        self._require("effect-attempted")
        self.phase = "observation-in-progress"
        try:
            if self.controls is None:
                raise ValueError("SA4 runtime controls are absent")
            self.controls.ensure_armed()
            with _fixed_bindings(self._values["plan"]):
                receipt = receipt_producer.observe(
                    self._values["plan"], self._values["admission"],
                    self._values["claim"], self._values["terminal"],
                    observed_epoch=observed_epoch)
        except BaseException:
            if self.controls is not None:
                self.controls.retain_uncertain()
            self.phase = "uncertain-manual-reconciliation-required"
            raise
        self._values["postcheck"] = receipt
        self.phase = "awaiting-postcheck-proof"
        return receipt

    def accept_postcheck_proof(self, proof_raw: bytes) -> str:
        """Verify externally signed observer evidence and choose one branch."""
        self._require("awaiting-postcheck-proof")
        claim = contract.decode_unique_json(self._values["claim"])
        try:
            result = receipt_validator.validate(
                self._values["postcheck"], proof_raw,
                not_before_epoch=claim["claimed_epoch"],
                deadline_epoch=claim["claim_deadline_epoch"])
        except BaseException:
            self.phase = "uncertain-manual-reconciliation-required"
            raise
        self._values["postcheck_proof"] = proof_raw
        self.phase = ("ready-to-reconcile" if result["postchecks_complete"]
                      else "rollback-required")
        return self.phase

    def rollback_once(self, *, rollback_attempt_id: str,
                      rollback_epoch: int, observed_epoch: int) -> bytes:
        """Restore once after a verified failed postcheck, then pause again."""
        self._require("rollback-required")
        claim = contract.decode_unique_json(self._values["claim"])
        try:
            if self.controls is None:
                raise ValueError("SA4 runtime controls are absent")
            self.controls.ensure_armed()
            with _fixed_bindings(self._values["plan"]):
                terminal = rollback_owner.restore(
                    self._values["plan"], self._values["checkpoint"],
                    self._values["terminal"], self._values["postcheck"],
                    self._values["postcheck_proof"],
                    rollback_attempt_id=rollback_attempt_id,
                    not_before_epoch=claim["claimed_epoch"],
                    deadline_epoch=claim["claim_deadline_epoch"],
                    rollback_epoch=rollback_epoch)
                rollback_terminal_raw = _raw(terminal)
                receipt = rollback_producer.observe(
                    self._values["plan"], self._values["admission"],
                    self._values["claim"], self._values["checkpoint"],
                    self._values["postcheck"], self._values["postcheck_proof"],
                    rollback_terminal_raw, observed_epoch=observed_epoch)
        except BaseException:
            if self.controls is not None:
                self.controls.retain_uncertain()
            self.phase = "uncertain-manual-reconciliation-required"
            raise
        self._values.update(rollback_terminal=rollback_terminal_raw,
                            rollback_receipt=receipt)
        self.phase = "awaiting-rollback-proof"
        return receipt

    def accept_rollback_proof(self, proof_raw: bytes) -> None:
        self._require("awaiting-rollback-proof")
        claim = contract.decode_unique_json(self._values["claim"])
        postcheck = contract.decode_unique_json(self._values["postcheck"])
        try:
            receipt_validator.validate_rollback(
                self._values["rollback_receipt"], proof_raw,
                not_before_epoch=postcheck["observed_epoch"],
                deadline_epoch=claim["claim_deadline_epoch"])
        except BaseException:
            self.phase = "uncertain-manual-reconciliation-required"
            raise
        self._values["rollback_proof"] = proof_raw
        self.phase = "ready-to-reconcile"

    def retained_evidence(self, name: str) -> bytes:
        """Return one already-produced evidence artifact, never authority."""
        allowed = {"rollback_terminal", "rollback_receipt", "rollback_proof"}
        if name not in allowed or name not in self._values:
            raise ValueError("SA4 retained evidence name changed")
        value = self._values[name]
        if not isinstance(value, bytes) or not value:
            raise ValueError("SA4 retained evidence value changed")
        return value

    def finish(self, *, now_epoch: int) -> dict[str, object]:
        """Burn the claim terminally; there is deliberately no retry method."""
        self._require("ready-to-reconcile")
        self.phase = "reconciliation-in-progress"
        try:
            if self.controls is None:
                raise ValueError("SA4 runtime controls are absent")
            self.controls.ensure_armed()
            result = reconciler.reconcile(
                self._values["plan"], self._values["source"],
                self._values["admission"], self._values["checkpoint"],
                self._values["terminal"], self._values["postcheck"],
                self._values["postcheck_proof"], self.ledger,
                now_epoch=now_epoch,
                rollback_terminal_raw=self._values.get("rollback_terminal"),
                rollback_receipt_raw=self._values.get("rollback_receipt"),
                rollback_proof_raw=self._values.get("rollback_proof"))
            self.controls.release_terminal()
        except BaseException:
            if self.controls is not None:
                self.controls.retain_uncertain()
            self.phase = "uncertain-manual-reconciliation-required"
            raise
        self.phase = "terminal"
        return result
