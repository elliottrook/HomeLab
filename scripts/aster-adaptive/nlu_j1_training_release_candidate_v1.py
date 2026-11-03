"""Validate the source-only J1 training release candidate without training."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nlu_j1_training_recipe_v1 as recipe
from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-j1-training-release-candidate.v1"
RECEIPT_NAMES = {"development-v1", *(f"calibration-v{i}" for i in range(1, 7))}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(raw: bytes, root: Path) -> dict[str, object]:
    value = decode_unique_json(raw)
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("J1 release-candidate schema changed")
    if (value.get("status") != "human-promotion-review-required"
            or value.get("authority") != "not-granted"
            or value.get("automatic_routing") != "off"
            or value.get("artifact") != {"artifact_sha256": None, "status": "not-trained"}):
        raise ValueError("J1 release candidate grants authority or claims an artifact")
    corpus = value.get("corpus", {})
    if (corpus.get("sha256") != recipe.CORPUS_SHA256
            or corpus.get("normalized_text_set_sha256") != recipe.CORPUS_TEXT_SET_SHA256
            or corpus.get("cases") != 400 or corpus.get("train") != 320
            or corpus.get("validation") != 80):
        raise ValueError("J1 release-candidate corpus binding changed")
    recipe_row = value.get("recipe", {})
    expected_source = sha(root / "nlu_j1_training_recipe_v1.py")
    expected_test = sha(root / "test_nlu_j1_training_recipe_v1.py")
    expected_manifest = hashlib.sha256(recipe.canonical(recipe.recipe_manifest())).hexdigest()
    if recipe_row != {"source_sha256": expected_source, "test_sha256": expected_test,
                      "manifest_sha256": expected_manifest}:
        raise ValueError("J1 release-candidate recipe binding changed")
    label = value.get("label_map", {})
    if (label.get("labels") != 16
            or label.get("source_sha256") != sha(root / "nlu_whole_label_choice_v1.py")
            or label.get("ontology_sha256")
            != hashlib.sha256(recipe.ontology._catalogue_text().encode()).hexdigest()):
        raise ValueError("J1 release-candidate label map changed")
    runtime = value.get("runtime_boundary", {})
    if (runtime.get("deterministic_guard_sha256")
            != sha(root / "nlu_deterministic_guard_v1.py")
            or runtime.get("deterministic_guard_required") is not True
            or runtime.get("model_output")
            != "one-known-label-plus-confidence-and-margin-with-guarded-projection"
            or runtime.get("tools") != "forbidden"):
        raise ValueError("J1 release-candidate runtime boundary changed")
    private = value.get("private_nonoverlap", {})
    hashes = private.get("receipt_hashes", {})
    if (set(hashes) != RECEIPT_NAMES
            or any(not isinstance(digest, str) or len(digest) != 64
                   or any(character not in "0123456789abcdef" for character in digest)
                   for digest in hashes.values())
            or private.get("status") != "complete"
            or private.get("sealed_holdout_read") is not False):
        raise ValueError("J1 release-candidate private receipt boundary changed")
    decision = value.get("decision", {})
    if (decision.get("public_gate") != "forbidden-before-artifact-freeze"
            or decision.get("sealed_holdout") != "forbidden"
            or decision.get("threshold_source") != "frozen-validation-only"
            or decision.get("margin_grid") != "0.000..1.000 step 0.005"
            or decision.get("minimum_validation_accepted") != 48
            or decision.get("deterministic_guard_required") is not True):
        raise ValueError("J1 release-candidate decision boundary changed")
    return {"schema": SCHEMA, "state": "valid", "artifact": "absent",
            "receipts": 7, "authority": "not-granted", "automatic_routing": "off"}


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    manifest = root / "fixtures/nlu-j1-training-recipe-release-candidate-v1.json"
    print(json.dumps(validate(manifest.read_bytes(), root), sort_keys=True,
                     separators=(",", ":")))
