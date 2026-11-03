import copy
import json
import math
import os
from pathlib import Path
import unittest

import nlu_j1_training_recipe_v1 as recipe

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "fixtures" / "nlu-j1-training-draft-v3.json"
RELEASE = ROOT / "fixtures" / "nlu-j1-training-recipe-release-candidate-v1.json"


class J1TrainingRecipeTests(unittest.TestCase):
    def rows(self):
        labels = sorted(recipe.ontology.CATALOGUE)
        return [{"id": "a", "text": "Turn on the hallway lamp", "label_id": labels[0]},
                {"id": "b", "text": "Explain why the sky is blue", "label_id": labels[1]}]

    def test_features_are_nonnegative_normalized_and_deterministic(self):
        one = recipe.feature_vector("  Explain   CAFÉ  ")
        self.assertEqual(one, recipe.feature_vector("explain café"))
        self.assertTrue(all(value > 0 for value in one.values()))
        self.assertAlmostEqual(1.0, sum(value * value for value in one.values()))

    def test_training_and_quantization_are_deterministic(self):
        one = recipe.train_rows(self.rows())
        two = recipe.train_rows(list(reversed(self.rows())))
        self.assertEqual(one, two)
        self.assertEqual(recipe.quantize_model(one[1]), recipe.quantize_model(two[1]))

    def test_unknown_label_duplicate_id_and_nonfinite_model_fail_closed(self):
        rows = self.rows(); rows[0]["label_id"] = "unknown"
        with self.assertRaises(ValueError): recipe.train_rows(rows)
        rows = self.rows(); rows[1]["id"] = rows[0]["id"]
        with self.assertRaises(ValueError): recipe.train_rows(rows)
        with self.assertRaises(ValueError):
            recipe.quantize_model({"defaults": [math.nan] * 16, "deltas": [{}] * 16})

    def test_threshold_is_strict_exact_unique_complete_and_finite(self):
        labels = sorted(recipe.ontology.CATALOGUE)
        rows = [
            {"id": "a", "label_id": labels[0], "expected_label_id": labels[0],
             "confidence": .9, "margin": .8, "guarded_exact": True},
            {"id": "b", "label_id": labels[1], "expected_label_id": labels[1],
             "confidence": .7, "margin": .6, "guarded_exact": True},
            {"id": "c", "label_id": labels[2], "expected_label_id": labels[3],
             "confidence": .6, "margin": .4, "guarded_exact": False},
        ]
        self.assertEqual(.405, recipe.select_threshold(rows, expected_count=3, minimum_accepted=2))
        for mutation in (lambda x: x[0].update(confidence=math.nan),
                         lambda x: x[1].update(id="a"),
                         lambda x: x[0].update(extra=True)):
            changed = copy.deepcopy(rows); mutation(changed)
            with self.assertRaises(ValueError):
                recipe.select_threshold(changed, expected_count=3, minimum_accepted=2)

    def test_artifact_roundtrip_projection_is_guarded_and_non_authorizing(self):
        labels, trained = recipe.train_rows(self.rows())
        digest, guard_digest = "a" * 64, "b" * 64
        value = recipe.artifact(labels, trained, margin_threshold=.5,
                                release_candidate_sha256=digest, guard_sha256=guard_digest)
        rebuilt = recipe.model_from_artifact(value, release_candidate_sha256=digest,
                                             guard_sha256=guard_digest,
                                             expected_artifact_sha256=value["artifact_sha256"])
        self.assertEqual(recipe.quantize_model(trained), rebuilt[1])
        result = recipe.project(value, "Explain why the sky is blue",
                                release_candidate_sha256=digest, guard_sha256=guard_digest,
                                expected_artifact_sha256=value["artifact_sha256"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])
        recipe.guard.contract._validate_semantics(result["interpretation"])

    def test_artifact_tamper_and_arbitrary_threshold_fail_closed(self):
        labels, trained = recipe.train_rows(self.rows())
        with self.assertRaises(ValueError):
            recipe.artifact(labels, trained, margin_threshold=.501,
                            release_candidate_sha256="a" * 64, guard_sha256="b" * 64)
        value = recipe.artifact(labels, trained, margin_threshold=.5,
                                release_candidate_sha256="a" * 64, guard_sha256="b" * 64)
        value["labels"][0]["default"] += .1
        with self.assertRaises(ValueError):
            recipe.model_from_artifact(value, release_candidate_sha256="a" * 64,
                                       guard_sha256="b" * 64,
                                       expected_artifact_sha256=value["artifact_sha256"])
        value = recipe.artifact(labels, trained, margin_threshold=.5,
                                release_candidate_sha256="a" * 64, guard_sha256="b" * 64)
        value["margin_threshold"] = -1.0
        copied = dict(value); copied.pop("artifact_sha256")
        value["artifact_sha256"] = recipe.hashlib.sha256(recipe.canonical(copied)).hexdigest()
        with self.assertRaises(ValueError):
            recipe.model_from_artifact(value, release_candidate_sha256="a" * 64,
                                       guard_sha256="b" * 64,
                                       expected_artifact_sha256=value["artifact_sha256"])

    def test_rejected_projection_keeps_deterministic_privacy_floor(self):
        labels, trained = recipe.train_rows(self.rows())
        value = recipe.artifact(labels, trained, margin_threshold=1.0,
                                release_candidate_sha256="a" * 64, guard_sha256="b" * 64)
        result = recipe.project(value, "Show my private medical appointments",
                                release_candidate_sha256="a" * 64, guard_sha256="b" * 64,
                                expected_artifact_sha256=value["artifact_sha256"])
        self.assertFalse(result["accepted"])
        self.assertEqual("personal", result["interpretation"]["sensitivity"])
        self.assertEqual("abstain", result["interpretation"]["disposition"])

    def test_manifest_forbids_evaluation_holdout_authority_and_network(self):
        value = recipe.recipe_manifest()
        self.assertEqual(48, value["minimum_validation_accepted"])
        self.assertEqual("forbidden", value["evaluation_inputs"])
        self.assertEqual("forbidden", value["sealed_holdout"])
        self.assertEqual("not-granted", value["authority"])
        self.assertEqual("off", value["automatic_routing"])
        json.dumps(value, allow_nan=False)

    def test_exact_end_to_end_when_private_review_is_available(self):
        private = os.environ.get("ASTER_J1_PRIVATE_REVIEW_DIR")
        if not private:
            self.skipTest("set ASTER_J1_PRIVATE_REVIEW_DIR for exact receipt-bound test")
        private = Path(private)
        receipts = {path.stem: path.read_bytes() for path in private.glob("*.json")
                    if path.name != "private-review-result.json"}
        model, summary = recipe.train_exact(
            CORPUS.read_bytes(), receipts,
            (private / "private-review-result.json").read_bytes(), RELEASE.read_bytes())
        self.assertEqual(70, summary["validation_exact"])
        self.assertEqual(70, summary["guarded_validation_exact"])
        self.assertGreaterEqual(summary["accepted_validation"], 48)
        self.assertEqual(summary["accepted_validation"], summary["accepted_validation_exact"])
        self.assertEqual(model["artifact_sha256"], summary["artifact_sha256"])

    def test_exact_training_rejects_missing_receipts(self):
        with self.assertRaises(ValueError):
            recipe.train_exact(CORPUS.read_bytes(), {}, b"{}", RELEASE.read_bytes())


if __name__ == "__main__":
    unittest.main()
