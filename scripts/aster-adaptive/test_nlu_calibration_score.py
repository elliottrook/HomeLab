import copy
import json
import unittest

import nlu_calibration_corpus as corpus
import nlu_calibration_score as score
from nlu_threshold_policy import FAMILIES, sha256

from test_nlu_calibration_corpus import DEVELOPMENT, encoded, labels, source


ENGINE = "1" * 64
POLICY = "2" * 64


def run_inputs():
    source_raw = encoded(source())
    label_value = labels(source_raw)
    label_value["labels"][0]["label"]["sensitivity"] = "personal"
    label_raw = encoded(label_value)
    release, _ = corpus.build_release(source_raw, label_raw, DEVELOPMENT)
    release_raw = encoded(release)
    label_by_id = {row["id"]: row["label"] for row in json.loads(label_raw)["labels"]}
    records = []
    for case_id, label in label_by_id.items():
        records.append({
            "id": case_id,
            "valid": True,
            "latency_seconds": 0.5,
            "interpretation": {
                "schema_version": "request-interpretation.v1",
                "request_id": case_id,
                "principal_ref": "nlu-calibration-v1",
                **label,
                "engine_digest": "sha256:" + ENGINE,
                "policy_digest": "sha256:" + POLICY,
                "confidence": None,
                "authorization": "not-granted",
            },
        })
    run = {
        "schema": score.RUN_SCHEMA,
        "candidate_bundle_sha256": corpus.CANDIDATE_SHA256,
        "calibration_artifact_sha256": sha256(release_raw),
        "engine_sha256": ENGINE,
        "policy_sha256": POLICY,
        "records": records,
        "authority": "not-granted",
    }
    return source_raw, label_raw, release_raw, run


class NluCalibrationScoreTests(unittest.TestCase):
    def derive(self, changes=None):
        source_raw, label_raw, release_raw, run = run_inputs()
        if changes:
            changes(run)
        return score.derive_score(
            source_raw, label_raw, release_raw, encoded(run), DEVELOPMENT,
            engine_sha256=ENGINE, policy_sha256=POLICY,
        )

    def test_binary_route_score_is_content_free_and_not_confidence(self):
        result = self.derive()
        self.assertEqual(60, len(result["cases"]))
        self.assertEqual({0.0, 1.0}, {row["route_score"] for row in result["cases"]})
        self.assertNotIn("confidence", json.dumps(result))
        self.assertNotIn("Synthetic calibration request", json.dumps(result))

    def test_wrong_route_is_a_selective_error_and_nonroute_is_unsafe_at_zero(self):
        def change(run):
            row = next(item for item in run["records"] if item["id"].startswith("cal-general-answer"))
            row["interpretation"]["sensitivity"] = "internal"
            nonroute = next(item for item in run["records"] if item["id"].startswith("cal-unsupported"))
            self.assertNotEqual("route", nonroute["interpretation"]["disposition"])
        result = self.derive(change)
        wrong = next(row for row in result["cases"] if row["id"].startswith("cal-general-answer"))
        self.assertEqual(1.0, wrong["route_score"])
        self.assertFalse(wrong["safe_and_correct_if_routed"])
        nonroute = next(row for row in result["cases"] if row["id"].startswith("cal-unsupported"))
        self.assertEqual(0.0, nonroute["route_score"])
        self.assertTrue(nonroute["unsafe_false_route_if_routed"])

    def test_privacy_underclassification_is_explicit(self):
        changed_id = None

        def change(run):
            nonlocal changed_id
            row = run["records"][0]
            changed_id = row["id"]
            row["interpretation"]["sensitivity"] = "public"
        result = self.derive(change)
        row = next(item for item in result["cases"] if item["id"] == changed_id)
        self.assertTrue(row["privacy_underclassified"])

    def test_invalid_result_stays_in_denominator_with_zero_score(self):
        def change(run):
            row = run["records"][0]
            row.clear()
            row.update({
                "id": "cal-household-command-00",
                "valid": False,
                "latency_seconds": 45.0,
                "failure": "timeout",
                "error_type": "deadline_exceeded",
            })
        result = self.derive(change)
        row = next(item for item in result["cases"] if item["id"] == "cal-household-command-00")
        self.assertEqual(0.0, row["route_score"])
        self.assertFalse(row["safe_and_correct_if_routed"])
        self.assertTrue(row["unsafe_false_route_if_routed"])

    def test_binding_drift_duplicates_and_authority_fail_closed(self):
        variants = [
            lambda run: run.update(candidate_bundle_sha256="0" * 64),
            lambda run: run.update(authority="granted"),
            lambda run: run["records"].__setitem__(1, copy.deepcopy(run["records"][0])),
            lambda run: run["records"][0]["interpretation"].update(confidence=0.9),
        ]
        for change in variants:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.derive(change)


if __name__ == "__main__":
    unittest.main()
