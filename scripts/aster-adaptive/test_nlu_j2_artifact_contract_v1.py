import copy
import hashlib
from pathlib import Path
import unittest

import nlu_j2_artifact_contract_v1 as artifact
import nlu_j2_training_recipe_manifest_v1 as recipe


CORPUS_RELEASE = "a" * 64
ADMISSION = "b" * 64


def value():
    boundary = recipe.expected_manifest()["runtime_boundary"]
    result = {
        "schema": "aster-nlu-j2-byte-conv-artifact.v1",
        "candidate_id": "j2-byte-conv-joint-v1",
        "training_recipe_sha256": artifact.RECIPE_SHA256,
        "preregistration_sha256": recipe.PREREGISTRATION_SHA256,
        "corpus_release_sha256": CORPUS_RELEASE,
        "training_admission_sha256": ADMISSION,
        "ontology_sha256": boundary["ontology_sha256"],
        "deterministic_guard_sha256": boundary["deterministic_guard_source_sha256"],
        "selected_epoch": 12, "threshold": 0.35,
        "validation_rows": 192, "accepted_validation_rows": 160,
        "validation_truth_sha256": "d" * 64,
        "validation_selection_sha256": "e" * 64,
        "validation_replay_sha256": "c" * 64,
        "tensors": {name: [0.0] * artifact._count(shape)
                    for name, shape in artifact.SHAPES.items()},
        "authority": "none", "automatic_routing": "off", "deployment": False,
    }
    result["artifact_sha256"] = artifact.artifact_sha256(result)
    return result


class J2ArtifactContractTests(unittest.TestCase):
    def test_recipe_pin_matches_frozen_fixture(self):
        fixture = (Path(__file__).parent / "fixtures" /
                   "nlu-j2-training-recipe-manifest-v1.json")
        self.assertEqual(artifact.RECIPE_SHA256,
                         hashlib.sha256(fixture.read_bytes()).hexdigest())

    def test_exact_synthetic_shape_is_valid_but_not_deployed(self):
        result = artifact.validate(artifact.canonical(value()),
                                   CORPUS_RELEASE, ADMISSION)
        self.assertEqual(46848, result["parameter_count"])
        self.assertTrue(result["replay_required"])
        self.assertFalse(result["deployment"])

    def test_tensor_shape_precision_and_nonfinite_fail_closed(self):
        variants = []
        changed = value(); changed["tensors"]["output-bias"].pop(); variants.append(changed)
        changed = value(); changed["tensors"]["output-bias"][0] = 0.12345678901; variants.append(changed)
        changed = value(); changed["tensors"]["output-bias"][0] = float("inf"); variants.append(changed)
        for changed in variants:
            with self.subTest(), self.assertRaises(ValueError):
                artifact.validate(artifact.canonical(changed), CORPUS_RELEASE, ADMISSION)

    def test_recipe_admission_threshold_and_self_hash_drift_fail_closed(self):
        variants = []
        changed = value(); changed["training_recipe_sha256"] = "0" * 64; variants.append(changed)
        changed = value(); changed["training_admission_sha256"] = "0" * 64; variants.append(changed)
        changed = value(); changed["threshold"] = 0.333; variants.append(changed)
        changed = value(); changed["artifact_sha256"] = "0" * 64; variants.append(changed)
        for changed in variants:
            with self.subTest(), self.assertRaises(ValueError):
                artifact.validate(artifact.canonical(changed), CORPUS_RELEASE, ADMISSION)

    def test_duplicate_and_unknown_fields_fail_closed(self):
        changed = value(); changed["optimizer_state"] = {}
        with self.assertRaises(ValueError):
            artifact.validate(artifact.canonical(changed), CORPUS_RELEASE, ADMISSION)
        raw = artifact.canonical(value()).replace(
            b'"deployment":false', b'"deployment":false,"deployment":false')
        with self.assertRaises(ValueError):
            artifact.validate(raw, CORPUS_RELEASE, ADMISSION)


if __name__ == "__main__": unittest.main()
