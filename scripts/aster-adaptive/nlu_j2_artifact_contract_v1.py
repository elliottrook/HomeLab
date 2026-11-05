"""Fail-closed contract for a future trained J2 artifact and replay binding."""
from __future__ import annotations

import hashlib
import json
import math
import re

import nlu_j2_reference_primitives_v1 as primitives
import nlu_j2_training_recipe_manifest_v1 as recipe
from nlu_threshold_policy import decode_unique_json


RECIPE_SHA256 = "71cb32f9b56f1fc725ae6c08a7f27c129e105cf458fb71c0fa743132a8e17f6c"
HEX64 = re.compile(r"[0-9a-f]{64}")
SHAPES = {name: shape for name, shape, *_ in primitives.PARAMETERS}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def artifact_sha256(value: dict[str, object]) -> str:
    copied = dict(value); copied.pop("artifact_sha256", None)
    return hashlib.sha256(canonical(copied)).hexdigest()


def _count(shape: tuple[int, ...]) -> int:
    result = 1
    for dimension in shape:
        result *= dimension
    return result


def validate(raw: bytes, expected_corpus_release_sha256: str,
             expected_training_admission_sha256: str) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "candidate_id", "training_recipe_sha256",
              "preregistration_sha256", "corpus_release_sha256",
              "training_admission_sha256", "ontology_sha256",
              "deterministic_guard_sha256", "selected_epoch", "threshold",
              "validation_rows", "accepted_validation_rows",
              "validation_replay_sha256", "tensors", "artifact_sha256",
              "authority", "automatic_routing", "deployment"}
    boundary = recipe.expected_manifest()["runtime_boundary"]
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-nlu-j2-byte-conv-artifact.v1"
            or value["candidate_id"] != "j2-byte-conv-joint-v1"
            or value["training_recipe_sha256"] != RECIPE_SHA256
            or value["preregistration_sha256"] != recipe.PREREGISTRATION_SHA256
            or not isinstance(expected_corpus_release_sha256, str)
            or not HEX64.fullmatch(expected_corpus_release_sha256)
            or value["corpus_release_sha256"] != expected_corpus_release_sha256
            or not isinstance(expected_training_admission_sha256, str)
            or not HEX64.fullmatch(expected_training_admission_sha256)
            or value["training_admission_sha256"]
            != expected_training_admission_sha256
            or value["ontology_sha256"] != boundary["ontology_sha256"]
            or value["deterministic_guard_sha256"]
            != boundary["deterministic_guard_source_sha256"]
            or type(value["selected_epoch"]) is not int
            or not 1 <= value["selected_epoch"] <= 40
            or type(value["threshold"]) not in {int, float}
            or not math.isfinite(value["threshold"])
            or not 0.0 <= value["threshold"] <= 1.0
            or abs(value["threshold"] * 200 - round(value["threshold"] * 200)) > 1e-12
            or value["validation_rows"] != 192
            or type(value["accepted_validation_rows"]) is not int
            or not 116 <= value["accepted_validation_rows"] <= 192
            or not isinstance(value["validation_replay_sha256"], str)
            or not HEX64.fullmatch(value["validation_replay_sha256"])
            or not isinstance(value["tensors"], dict)
            or set(value["tensors"]) != set(SHAPES)
            or value["authority"] != "none"
            or value["automatic_routing"] != "off"
            or value["deployment"] is not False):
        raise ValueError("J2 artifact binding changed")
    for name, shape in SHAPES.items():
        tensor = value["tensors"][name]
        if (not isinstance(tensor, list) or len(tensor) != _count(shape)
                or any(type(item) not in {int, float}
                       or not math.isfinite(item)
                       or round(item, 10) != item for item in tensor)):
            raise ValueError("J2 artifact tensor changed")
    if (not isinstance(value["artifact_sha256"], str)
            or value["artifact_sha256"] != artifact_sha256(value)):
        raise ValueError("J2 artifact self-hash changed")
    return {"schema": "aster-nlu-j2-artifact-validation.v1",
            "candidate_id": value["candidate_id"],
            "artifact_sha256": value["artifact_sha256"],
            "selected_epoch": value["selected_epoch"],
            "threshold": value["threshold"],
            "validation_rows": 192,
            "accepted_validation_rows": value["accepted_validation_rows"],
            "parameter_count": sum(_count(shape) for shape in SHAPES.values()),
            "replay_required": True, "deployment": False,
            "authority": "none", "automatic_routing": "off"}
