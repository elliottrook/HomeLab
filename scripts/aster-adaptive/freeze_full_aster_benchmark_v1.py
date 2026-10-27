"""Build, without effects, an owner-frozen full-Aster benchmark contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import full_aster_benchmark_contract_v1 as final_contract
import full_aster_benchmark_proposal_v1 as proposal_contract


SCHEMA = "aster-full-path-benchmark-freeze-input.v1"
HEX = set("0123456789abcdef")


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX


def canonical_sha(document):
    raw = json.dumps(document, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def freeze(proposal, freeze_input):
    proposal_contract.validate(proposal)
    if (not isinstance(freeze_input, dict)
            or set(freeze_input) != {"schema", "proposal_sha256", "case_packet",
                                     "challenger", "owner_acceptance"}
            or freeze_input["schema"] != SCHEMA
            or freeze_input["proposal_sha256"] != canonical_sha(proposal)):
        raise ValueError("freeze input or proposal binding differs")

    packet = freeze_input["case_packet"]
    family_counts = {family: 4 for family in proposal_contract.FAMILIES}
    if (not isinstance(packet, dict)
            or packet != {"sha256": packet.get("sha256"), "cases": 24,
                          "families": family_counts}
            or not _sha(packet.get("sha256"))):
        raise ValueError("owner packet binding differs")

    challenger = freeze_input["challenger"]
    if (not isinstance(challenger, dict)
            or set(challenger) != {"identity_sha256", "runtime_sha256", "mode"}
            or not _sha(challenger["identity_sha256"])
            or not _sha(challenger["runtime_sha256"])
            or challenger["mode"] != "reasoning-on-27b-plus"):
        raise ValueError("challenger pin differs")

    acceptance = freeze_input["owner_acceptance"]
    if (not isinstance(acceptance, dict)
            or set(acceptance) != {"decision", "proposal_sha256", "record_sha256"}
            or acceptance["decision"] != "accepted"
            or acceptance["proposal_sha256"] != freeze_input["proposal_sha256"]
            or not _sha(acceptance["record_sha256"])):
        raise ValueError("owner acceptance differs")

    proposed = proposal["proposed_contract"]
    minimum = proposed["quality"]["minimum_by_family"]
    baseline = proposal["baseline"]
    document = {
        "schema": final_contract.SCHEMA,
        "status": "owner-frozen",
        "case_packet": packet,
        "models": {
            "baseline": {"identity_sha256": baseline["model_sha256"],
                         "runtime_sha256": baseline["runtime_sha256"],
                         "mode": baseline["mode"]},
            "challenger": challenger,
        },
        "quality": {"minimum_overall": proposed["quality"]["minimum_overall"],
                    "minimum_by_family": {family: minimum for family in family_counts},
                    "reviewer_count": proposed["quality"]["reviewer_count"]},
        "safety": proposed["safety"],
        "latency": proposed["latency"],
        "resources": proposed["resources"],
        "comparability": {"same_inputs": True, "same_retrieval_snapshot": True,
                          "same_response_schema": True, "same_retry_policy": True,
                          "reasoning_retained": False},
        "recovery": {"f6_required": True, "exact_baseline_restore": True,
                     "independent_observer_required": True,
                     "uncertain_recovery_rejects_result": True},
        "authority": "not-granted",
    }
    return final_contract.validate(document)


def load_json(path: Path):
    return json.loads(path.read_bytes())
