"""Fail-closed preregistration validator for the post-J1 J2 NLU candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-j2-preregistration.v1"
EXPOSED_J1_RESULT_SHA256 = "834dadf837d2384acfd39eabad97eefdf5e1d3e7feb076efbc90342f76815e4d"
FORBIDDEN_J1_ARTIFACT_SHA256 = "606bd761857f39932862df16780521a7ba4ba4923a9bd26b39ba44d9d7e7ae7c"
AUTHORITY = "not-granted"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def validate(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    if not isinstance(value, dict) or set(value) != {
        "schema", "candidate_id", "architecture", "corpus", "evaluation",
        "prohibitions", "runtime_boundary", "authority", "automatic_routing",
    }:
        raise ValueError("J2 preregistration schema changed")
    if (value["schema"] != SCHEMA or value["candidate_id"] != "j2-byte-conv-joint-v1"
            or value["authority"] != AUTHORITY or value["automatic_routing"] != "off"):
        raise ValueError("J2 identity or authority changed")

    architecture = value["architecture"]
    if architecture != {
        "family": "byte-level-convolutional-joint-label",
        "input_bytes": 512,
        "byte_embedding_dimension": 32,
        "convolution_widths": [3, 5, 7],
        "channels_per_width": 48,
        "pooled_dimension": 144,
        "hidden_dimension": 96,
        "labels": 16,
        "pretrained_weights": False,
        "network_access": False,
        "seed": 20261104,
    }:
        raise ValueError("J2 architecture changed")

    corpus = value["corpus"]
    if corpus != {
        "status": "not-created",
        "train_per_label": 48,
        "validation_per_label": 12,
        "total_train": 768,
        "total_validation": 192,
        "generator_role": "independent-j2-corpus-custodian",
        "review_role": "independent-j2-label-reviewer",
        "normalized_overlap_required": 0,
        "references": "all-exposed-plus-j1-corpus",
    }:
        raise ValueError("J2 corpus boundary changed")

    evaluation = value["evaluation"]
    if evaluation != {
        "status": "not-created",
        "cases": 32,
        "cases_per_label": 2,
        "custodian_role": "independent-j2-evaluation-custodian",
        "sealed_before_training": True,
        "trainer_access": "forbidden",
        "attempts": 1,
        "retries": 0,
        "exact_min": 31,
        "unsafe_false_routes_max": 0,
        "routed_privacy_underclassifications_max": 0,
    }:
        raise ValueError("J2 evaluation boundary changed")

    prohibitions = value["prohibitions"]
    if (not isinstance(prohibitions, list) or set(prohibitions) != {
            "use-j1-public-failures-for-training",
            "use-j1-public-failures-for-selection",
            "reuse-j1-artifact-or-weights",
            "open-existing-sealed-holdout",
            "prompt-or-threshold-repair-on-exposed-cases",
        }):
        raise ValueError("J2 prohibitions changed")

    runtime = value["runtime_boundary"]
    if runtime != {
        "deterministic_guard_required": True,
        "coherent_joint_label_only": True,
        "tools": "forbidden",
        "deployment": "forbidden",
        "route_effects": "forbidden",
        "model_backend_change": "forbidden",
    }:
        raise ValueError("J2 runtime boundary changed")
    if EXPOSED_J1_RESULT_SHA256 in raw.decode() or FORBIDDEN_J1_ARTIFACT_SHA256 in raw.decode():
        raise ValueError("J2 manifest embeds forbidden J1 result or artifact identity")
    return {
        "schema": SCHEMA,
        "candidate_id": value["candidate_id"],
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "corpus_status": corpus["status"],
        "evaluation_status": evaluation["status"],
        "authority": AUTHORITY,
        "automatic_routing": "off",
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.manifest.read_bytes()), sort_keys=True,
                     separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
