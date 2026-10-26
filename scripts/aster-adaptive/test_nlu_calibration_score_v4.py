import json
import unittest
from unittest import mock

import nlu_calibration_corpus_v4 as corpus
import nlu_calibration_score_v4 as score
from nlu_threshold_policy import sha256
from test_nlu_calibration_corpus_v4 import (
    DEVELOPMENT, encoded, labels, manifest, source,
)


ENGINE = "1" * 64
POLICY = "2" * 64


def bindings(source_raw, label_raw, manifest_raw):
    texts = sorted(
        corpus.base.normalized_text(case["text"])
        for case in json.loads(source_raw)["cases"]
    )
    return mock.patch.multiple(
        corpus,
        EXPECTED_SOURCE_SHA256=sha256(source_raw),
        EXPECTED_LABEL_SHA256=sha256(label_raw),
        EXPECTED_MANIFEST_SHA256=sha256(manifest_raw),
        EXPECTED_DEVELOPMENT_SHA256=sha256(DEVELOPMENT),
        EXPECTED_NORMALIZED_TEXT_SET_SHA256=sha256(
            ("\n".join(texts) + "\n").encode()
        ),
    )


def inputs():
    source_raw = encoded(source())
    label_raw = encoded(labels(source_raw))
    manifest_raw = encoded(manifest(source_raw))
    with bindings(source_raw, label_raw, manifest_raw):
        release, _ = corpus.build_release(
            source_raw, label_raw, manifest_raw, DEVELOPMENT
        )
    release_raw = encoded(release)
    gold = {row["id"]: row["label"] for row in json.loads(label_raw)["labels"]}
    records = [{
        "id": case_id,
        "valid": True,
        "latency_seconds": 0.5,
        "interpretation": {
            "schema_version": "request-interpretation.v1",
            "request_id": case_id,
            "principal_ref": "nlu-calibration-v4",
            **label,
            "engine_digest": "sha256:" + ENGINE,
            "policy_digest": "sha256:" + POLICY,
            "confidence": None,
            "authorization": "not-granted",
        },
    } for case_id, label in gold.items()]
    run = {
        "schema": score.RUN_SCHEMA,
        "candidate_bundle_sha256": corpus.CANDIDATE_SHA256,
        "calibration_artifact_sha256": sha256(release_raw),
        "engine_sha256": ENGINE,
        "policy_sha256": POLICY,
        "records": records,
        "authority": "not-granted",
    }
    journal = [{
        "event": "run_started",
        "schema": "aster-nlu-calibration-attempt-journal.v1",
        "candidate_bundle_sha256": corpus.CANDIDATE_SHA256,
        "calibration_artifact_sha256": sha256(release_raw),
        "planned": 60,
        "authority": "not-granted",
    }]
    for row in records:
        journal.extend((
            {"event": "attempt_started", "case_id": row["id"]},
            {"event": "attempt_recorded", "case_id": row["id"], "valid": True},
        ))
    journal.append({
        "event": "run_finished", "attempted": 60, "complete": True,
    })
    journal_raw = b"".join(encoded(row) for row in journal)
    return source_raw, label_raw, manifest_raw, release_raw, run, journal_raw


class NluCalibrationScoreV4Tests(unittest.TestCase):
    def derive(self, invalid_first=False):
        source_raw, label_raw, manifest_raw, release_raw, run, journal_raw = inputs()
        if invalid_first:
            row = run["records"][0]
            case_id = row["id"]
            row.clear()
            row.update({
                "id": case_id, "valid": False, "latency_seconds": 0.5,
                "failure": "invalid_response", "error_type": "response_invalid",
            })
            events = journal_raw.splitlines()
            events[2] = encoded({
                "event": "attempt_recorded", "case_id": case_id,
                "valid": False, "error_type": "response_invalid",
            }).rstrip(b"\n")
            journal_raw = b"\n".join(events) + b"\n"
        with bindings(source_raw, label_raw, manifest_raw):
            return score.derive_score(
                source_raw, label_raw, manifest_raw, release_raw,
                encoded(run), journal_raw, DEVELOPMENT,
                engine_sha256=ENGINE, policy_sha256=POLICY,
            )

    def test_exact_results_produce_sixty_content_free_rows(self):
        result = self.derive()
        self.assertEqual(60, len(result["cases"]))
        self.assertTrue(all(
            row["safe_and_correct_if_routed"]
            for row in result["cases"] if row["route_score"] == 1.0
        ))
        self.assertNotIn("Fresh synthetic v3 request", json.dumps(result))

    def test_manifest_binding_is_required(self):
        source_raw, label_raw, manifest_raw, release_raw, run, journal_raw = inputs()
        with bindings(source_raw, label_raw, manifest_raw), self.assertRaisesRegex(
            ValueError, "manifest"
        ):
            score.derive_score(
                source_raw, label_raw, manifest_raw + b" ", release_raw,
                encoded(run), journal_raw, DEVELOPMENT,
                engine_sha256=ENGINE, policy_sha256=POLICY,
            )

    def test_invalid_model_response_stays_in_denominator(self):
        result = self.derive(invalid_first=True)
        self.assertEqual(60, len(result["cases"]))
        target = source()["cases"][0]["id"]
        row = next(item for item in result["cases"] if item["id"] == target)
        self.assertEqual(0.0, row["route_score"])
        self.assertFalse(row["safe_and_correct_if_routed"])


if __name__ == "__main__":
    unittest.main()
