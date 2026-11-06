"""One-process SA4 transaction sequencing with an external observer signer."""
from __future__ import annotations

import hashlib
import re
from typing import Callable

import sa4_observer_signer_v1 as observer
import sa4_root_transaction_owner_v1 as root_owner
import sa4_single_file_repair_contract_v1 as contract


SIGNATURE = re.compile(r"[0-9a-f]{512}")
EPOCH_FIELDS = {
    "measurement", "checkpoint", "claim", "claim_deadline", "effect",
    "observation", "rollback", "rollback_observation", "finish",
}


def _proof(receipt_raw: bytes, signer: Callable[[bytes], str]) -> bytes:
    statement = observer.canonical({
        "schema": "aster-sa4-independent-receipt-proof.v1",
        "receipt_sha256": hashlib.sha256(receipt_raw).hexdigest(),
        "observer_id": observer.OBSERVER_ID,
        "observer_key_sha256": observer.KEY_SHA256,
        "signature_algorithm": "rsa-pkcs1v1_5-sha256",
        "authority": "observer-proof-only-no-effect",
    })
    observer.validate_statement(statement)
    signature = signer(statement)
    if not isinstance(signature, str) or not SIGNATURE.fullmatch(signature):
        raise ValueError("SA4 observer signature shape changed")
    value = contract.decode_unique_json(statement)
    return contract.canonical({**value, "signature_hex": signature})


def run(owner: root_owner.RootTransactionOwner, packet: dict[str, bytes],
        candidate_raw: bytes, epochs: dict[str, int], *,
        observer_signer: Callable[[bytes], str]) -> dict[str, object]:
    """Run exactly one owner transaction; there is deliberately no retry."""
    fields = {"plan", "approval", "approval_proof", "grant", "grant_proof"}
    if (not isinstance(owner, root_owner.RootTransactionOwner)
            or not isinstance(packet, dict) or set(packet) != fields
            or any(not isinstance(packet[name], bytes) for name in fields)
            or not isinstance(candidate_raw, bytes)
            or not isinstance(epochs, dict) or set(epochs) != EPOCH_FIELDS
            or any(type(value) is not int or value < 1
                   for value in epochs.values())):
        raise ValueError("SA4 one-shot controller input changed")
    owner.prepare(
        packet["plan"], packet["approval"], packet["approval_proof"],
        packet["grant"], packet["grant_proof"], candidate_raw,
        measurement_epoch=epochs["measurement"],
        checkpoint_epoch=epochs["checkpoint"])
    owner.execute_once(
        claim_epoch=epochs["claim"],
        claim_deadline_epoch=epochs["claim_deadline"],
        effect_epoch=epochs["effect"])
    postcheck_raw = owner.observe(observed_epoch=epochs["observation"])
    branch = owner.accept_postcheck_proof(
        _proof(postcheck_raw, observer_signer))
    rollback = branch == "rollback-required"
    if rollback:
        rollback_raw = owner.rollback_once(
            rollback_attempt_id=f"{owner.operation_id}-rollback",
            rollback_epoch=epochs["rollback"],
            observed_epoch=epochs["rollback_observation"])
        owner.accept_rollback_proof(_proof(rollback_raw, observer_signer))
    elif branch != "ready-to-reconcile":
        raise ValueError("SA4 one-shot controller branch changed")
    terminal = owner.finish(now_epoch=epochs["finish"])
    if owner.phase != "terminal" or not isinstance(terminal, dict):
        raise ValueError("SA4 one-shot controller did not terminate")
    return {
        "schema": "aster-sa4-one-shot-transaction-result.v1",
        "operation_id": owner.operation_id,
        "branch": "rollback" if rollback else "postcheck-complete",
        "observer_signatures": 2 if rollback else 1,
        "automatic_retry": False,
        "terminal_result_sha256": hashlib.sha256(
            contract.canonical(terminal)).hexdigest(),
    }
