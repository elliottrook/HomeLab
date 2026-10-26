import copy
import contextlib
import io
import json
import stat
import tempfile
import unittest
from pathlib import Path

import nlu_calibration_corpus as corpus
import nlu_calibration_score as score
from nlu_threshold_policy import FAMILIES, sha256

from test_nlu_calibration_corpus import DEVELOPMENT, encoded, labels, source


ENGINE = "1" * 64
POLICY = "2" * 64


def journal_for(run, release_raw):
    journal = [{
        "event": "run_started",
        "schema": "aster-nlu-calibration-attempt-journal.v1",
        "candidate_bundle_sha256": run["candidate_bundle_sha256"],
        "calibration_artifact_sha256": sha256(release_raw),
        "planned": 60,
        "authority": "not-granted",
    }]
    for record in run["records"]:
        journal.append({"event": "attempt_started", "case_id": record["id"]})
        event = {
            "event": "attempt_recorded",
            "case_id": record["id"],
            "valid": record["valid"],
        }
        if not record["valid"]:
            event["error_type"] = record["error_type"]
        journal.append(event)
    journal.append({
        "event": "run_finished", "attempted": len(run["records"]), "complete": True,
    })
    return b"".join(encoded(row) for row in journal)


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
    return source_raw, label_raw, release_raw, run, journal_for(run, release_raw)


class NluCalibrationScoreTests(unittest.TestCase):
    def derive(self, changes=None):
        source_raw, label_raw, release_raw, run, _ = run_inputs()
        if changes:
            changes(run)
        journal_raw = journal_for(run, release_raw)
        return score.derive_score(
            source_raw, label_raw, release_raw, encoded(run), journal_raw, DEVELOPMENT,
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
                "latency_seconds": 1.0,
                "failure": "invalid_response",
                "error_type": "response_invalid",
            })
        result = self.derive(change)
        row = next(item for item in result["cases"] if item["id"] == "cal-household-command-00")
        self.assertEqual(0.0, row["route_score"])
        self.assertFalse(row["safe_and_correct_if_routed"])
        self.assertTrue(row["unsafe_false_route_if_routed"])

    def test_infrastructure_failures_cannot_be_scored_as_complete(self):
        failures = [
            ("timeout", "deadline_exceeded"),
            ("engine_error", "engine_unavailable"),
            ("engine_error", "transport_error"),
        ]
        for failure, error_type in failures:
            def change(run):
                row = run["records"][-1]
                case_id = row["id"]
                row.clear()
                row.update({
                    "id": case_id,
                    "valid": False,
                    "latency_seconds": 1.0,
                    "failure": failure,
                    "error_type": error_type,
                })

            with self.subTest(error_type=error_type), self.assertRaisesRegex(
                ValueError, "infrastructure failure"
            ):
                self.derive(change)

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

    def test_attempt_journal_must_match_every_final_record(self):
        source_raw, label_raw, release_raw, run, journal_raw = run_inputs()
        changed = journal_raw.replace(
            run["records"][0]["id"].encode(), b"CAL-UNKNOWN", 1
        )
        with self.assertRaisesRegex(ValueError, "journal"):
            score.derive_score(
                source_raw, label_raw, release_raw, encoded(run), changed, DEVELOPMENT,
                engine_sha256=ENGINE, policy_sha256=POLICY,
            )

    def test_attempt_journal_digest_is_bound_into_score(self):
        source_raw, label_raw, release_raw, run, journal_raw = run_inputs()
        result = score.derive_score(
            source_raw, label_raw, release_raw, encoded(run), journal_raw, DEVELOPMENT,
            engine_sha256=ENGINE, policy_sha256=POLICY,
        )
        self.assertEqual(sha256(journal_raw), result["attempt_journal_sha256"])

    def test_cli_creates_owner_only_score_and_refuses_overwrite(self):
        source_raw, label_raw, release_raw, run, _ = run_inputs()
        run["engine_sha256"] = score.SEALED_ENGINE_SHA256
        run["policy_sha256"] = score.SEALED_POLICY_SHA256
        for row in run["records"]:
            row["interpretation"]["engine_digest"] = "sha256:" + score.SEALED_ENGINE_SHA256
            row["interpretation"]["policy_digest"] = "sha256:" + score.SEALED_POLICY_SHA256
        journal_raw = journal_for(run, release_raw)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                "source": source_raw,
                "labels": label_raw,
                "release": release_raw,
                "run": encoded(run),
                "journal": journal_raw,
                "development": DEVELOPMENT,
            }
            for name, raw in paths.items():
                (root / f"{name}.json").write_bytes(raw)
            output = root / "score.json"
            argv = [
                "--source", str(root / "source.json"),
                "--labels", str(root / "labels.json"),
                "--release", str(root / "release.json"),
                "--run", str(root / "run.json"),
                "--journal", str(root / "journal.json"),
                "--development", str(root / "development.json"),
                "--output", str(output),
            ]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, score.main(argv))
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            self.assertEqual(score.SCORE_SCHEMA, json.loads(output.read_bytes())["schema"])
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    score.main(argv)


if __name__ == "__main__":
    unittest.main()
