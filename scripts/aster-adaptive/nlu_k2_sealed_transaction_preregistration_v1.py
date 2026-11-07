"""Frozen non-authorizing contract for one K2 sealed-evaluation transaction."""
from __future__ import annotations

import hashlib
import json
import re


SCHEMA = "aster-nlu-k2-sealed-transaction-preregistration.v1"
WORKLOAD_ID = "m3-k2-sealed-evaluation-v1"
BOOKING_ID = re.compile(
    r"aster-stream-a-m3-k2-sealed-[0-9]{8}-[0-9]{4}-r[1-9][0-9]*\Z"
)
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def artifact() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "candidate_id": "k2-fixed-shortlist-9b-arbitration-v1",
        "workload_id": WORKLOAD_ID,
        "prerequisite": {
            "development_booking_id":
                "aster-stream-a-m3-k2-20261106-2000-r1",
            "development_state": "complete",
            "development_gate_passed": True,
            "development_status": "pass",
            "production_restored": True,
        },
        "private_inputs": {
            "macbook_corpus_path":
                "/private/tmp/aster-j2-evaluation-custodian-20261106-r5/inputs/corpus.json",
            "corpus_sha256":
                "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a",
            "macbook_evaluation_path":
                "/private/tmp/aster-j2-evaluation-custodian-20261106-r5/private/sealed-evaluation.json",
            "evaluation_sha256":
                "78f7b8aa7b8f8202e38333be4d497a489c1f36b3c6209839c05ecd3975191cae",
            "evaluation_mode": "0600",
            "expected_labels_leave_macbook": False,
            "text_retention_outside_macbook": False,
        },
        "runtime_pins": {
            "nlu_k2_apple_embedding_sealed_shortlister_v1.swift":
                "cf06a32a53ac1d76a9da47f7b7262ad9c7a10ec494685215d7e612369a877077",
            "nlu_k2_sealed_evaluation_runner_v1.py":
                "ca802811dd700e164bbd538735e2d0c670b5d1f841a1947e36cde7e3aa221a1a",
            "nlu_k2_sealed_relay_v1.py":
                "bd39e387219994611b28e53fdc527de337cce98c01fd08061fe343d7bfeb0c78",
            "nlu_k2_sealed_macbook_wrapper_v1.py":
                "e3880b4112f98333bcca3bca97a58850473e4df353a940f6c08dfa2d6866d2d2",
            "nlu_k2_sealed_coordinator_v1.py":
                "e5fa5e6a37c94516bafb3660d67bf0dadc26ac7f006a6fdceab4802dd4241861",
            "nlu_k2_sealed_evaluation_scorer_v1.py":
                "f28a1e0e364edbf97be6fc0f4f32ac0955571d2dd9718f65f39f9ca6d1bab873",
            "nlu_k2_consensus_policy_v1.py":
                "9027abbcc446d9c63100178e3ce9add60275a1f134bde9d7beeb30aa4a4d504e",
            "nlu_k2_shortlist_arbitrator_v1.py":
                "7c81894da9adbd1c3ee22b97d1487fcf2feadc1e4bc1e321a7c715479c517962",
            "nlu_deterministic_guard_v1.py":
                "d7d62d19008519ae50aa9b46799ab1f277a51904f2e80e65c30517abca8a7135",
            "nlu_local_model_adapter.py":
                "3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0",
            "nlu_whole_label_choice_v1.py":
                "6e7ee332ce74a44a5bb19877f9f8f0c90f814687279b3c4993fbb93fbd58948a",
            "nlu_threshold_policy.py":
                "984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d",
        },
        "network": {
            "macbook_runner_endpoint":
                "http://127.0.0.1:11437/v1/chat/completions",
            "mac_mini_relay_bind": "127.0.0.1:11438",
            "mac_mini_upstream_tunnel": "127.0.0.1:11439",
            "control_direction": "mac-mini-to-macbook-existing-ssh",
            "reverse_tunnel_bind": "macbook-loopback-only",
            "upstream_tunnel_bind": "mac-mini-loopback-only",
            "direct_macbook_b60": False,
            "new_access_grant": False,
            "standing_b60_credential_on_macbook": False,
        },
        "effect": {
            "cases": 32,
            "model_requests": 32,
            "retries": 0,
            "response_errors": 0,
            "per_request_timeout_seconds": 45,
            "deadline_seconds": 1800,
            "minimum_booking_seconds": 2700,
            "recovery_reserve_seconds": 900,
            "lease_required": True,
            "operation_lock_required": True,
            "registered_hash_pinned_workload_required": True,
            "transaction_nonces": 2,
            "tools": False,
            "route_effect": False,
        },
        "success": {
            "private_shortlist_rows": 32,
            "private_result_rows": 32,
            "content_free_metrics": True,
            "production_restored": True,
            "lease_ready": True,
            "locks_absent": True,
            "tunnels_absent": True,
            "relay_absent": True,
            "runner_absent": True,
            "private_listener_absent": True,
        },
        "authority": "not-granted",
        "effect_authorized": False,
        "automatic_routing": "off",
        "deployment": False,
    }


def validate(value: object) -> dict[str, object]:
    expected = artifact()
    if value != expected:
        raise ValueError("K2 sealed transaction preregistration changed")
    pins = value["runtime_pins"]
    if (len(pins) != 12
            or any(not isinstance(digest, str) or HEX64.fullmatch(digest) is None
                   for digest in pins.values())):
        raise ValueError("K2 sealed transaction runtime pins changed")
    return {
        "schema": "aster-nlu-k2-sealed-transaction-preregistration-summary.v1",
        "workload_id": WORKLOAD_ID,
        "runtime_pins": len(pins),
        "cases": 32,
        "model_requests": 32,
        "effect_authorized": False,
        "authority": "not-granted",
        "preregistration_sha256": hashlib.sha256(canonical(value)).hexdigest(),
    }


def validate_booking_id(value: str) -> str:
    if not isinstance(value, str) or BOOKING_ID.fullmatch(value) is None:
        raise ValueError("K2 sealed booking identity changed")
    return value


if __name__ == "__main__":
    print(canonical(validate(artifact())).decode(), end="")
