import copy
import contextlib
import io
import json
import stat
import tempfile
import unittest
from pathlib import Path

import nlu_calibration_corpus as corpus
from nlu_threshold_policy import FAMILIES, sha256


HERE = Path(__file__).parent
DEVELOPMENT = (HERE / "fixtures" / "nlu-development-v1.json").read_bytes()


def encoded(value):
    return corpus.canonical_json(value)


def source():
    cases = []
    for family in FAMILIES:
        for number in range(10):
            cases.append({
                "id": f"cal-{family}-{number:02d}",
                "family": family,
                "text": f"Synthetic calibration request {family} number {number}",
            })
    return {
        "schema": corpus.SOURCE_SCHEMA,
        "data_class": "synthetic",
        "evidence_class": "disjoint-calibration",
        "candidate_bundle_sha256": corpus.CANDIDATE_SHA256,
        "accepted_decision_sha256": corpus.DECISION_SHA256,
        "cases": cases,
    }


def labels(source_raw):
    value = json.loads(source_raw)
    rows = []
    for case in value["cases"]:
        unsupported = case["family"] == "unsupported"
        rows.append({
            "id": case["id"],
            "label": {
                "request_family": case["family"],
                "sensitivity": "public",
                "capability_needs": [],
                "ambiguity": "clear",
                "disposition": "abstain" if unsupported else "route",
                "reason": "unsupported" if unsupported else "understood",
            },
        })
    return {
        "schema": corpus.LABEL_SCHEMA,
        "source_sha256": sha256(source_raw),
        "reviewer": corpus.LABEL_REVIEWER,
        "labels": rows,
    }


class NluCalibrationCorpusTests(unittest.TestCase):
    def test_exact_balanced_source_and_labels_build_content_free_release(self):
        source_raw = encoded(source())
        release, summary = corpus.build_release(
            source_raw, encoded(labels(source_raw)), DEVELOPMENT
        )
        self.assertEqual(60, summary["case_count"])
        self.assertEqual({family: 10 for family in FAMILIES}, summary["family_counts"])
        self.assertEqual(60, len(release["cases"]))
        self.assertEqual("not-granted", release["authority"])
        serialized = json.dumps(release)
        self.assertNotIn("Synthetic calibration request", serialized)
        self.assertTrue(all(set(row) == {
            "id", "family", "case_sha256", "label_sha256",
            "review_receipt_sha256",
        } for row in release["cases"]))

    def test_changed_candidate_balance_overlap_and_duplicate_text_fail(self):
        value = source()
        value["candidate_bundle_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "candidate changed"):
            corpus.validate_source(encoded(value), DEVELOPMENT)
        value = source()
        value["cases"][0]["family"] = "general-answer"
        with self.assertRaisesRegex(ValueError, "ten cases"):
            corpus.validate_source(encoded(value), DEVELOPMENT)
        value = source()
        value["cases"][0]["text"] = value["cases"][1]["text"].upper()
        with self.assertRaisesRegex(ValueError, "duplicate normalized"):
            corpus.validate_source(encoded(value), DEVELOPMENT)
        value = source()
        development = json.loads(DEVELOPMENT)
        value["cases"][0]["text"] = development["cases"][0]["text"]
        with self.assertRaisesRegex(ValueError, "overlaps development"):
            corpus.validate_source(encoded(value), DEVELOPMENT)

    def test_label_reviewer_source_binding_and_semantics_fail_closed(self):
        source_raw = encoded(source())
        value = labels(source_raw)
        value["reviewer"] = corpus.CASE_CUSTODIAN
        with self.assertRaisesRegex(ValueError, "independent reviewer"):
            corpus.build_release(source_raw, encoded(value), DEVELOPMENT)
        value = labels(source_raw)
        value["labels"][0]["label"]["request_family"] = "general-answer"
        with self.assertRaisesRegex(ValueError, "family does not match"):
            corpus.build_release(source_raw, encoded(value), DEVELOPMENT)
        value = labels(source_raw)
        value["labels"][0]["label"]["capability_needs"] = ["shell.execute"]
        with self.assertRaisesRegex(ValueError, "capability"):
            corpus.build_release(source_raw, encoded(value), DEVELOPMENT)

    def test_duplicate_keys_and_raw_label_fields_are_rejected(self):
        source_raw = encoded(source())
        duplicate = source_raw.replace(
            b'"schema":"aster-nlu-calibration-cases.v1"',
            b'"schema":"aster-nlu-calibration-cases.v1","schema":"duplicate"',
        )
        with self.assertRaisesRegex(ValueError, "unique-key"):
            corpus.validate_source(duplicate, DEVELOPMENT)
        value = labels(source_raw)
        value["labels"][0]["label"]["text"] = "forbidden"
        with self.assertRaisesRegex(ValueError, "dimensions"):
            corpus.build_release(source_raw, encoded(value), DEVELOPMENT)

    def test_cli_creates_owner_only_release_and_refuses_overwrite(self):
        source_raw = encoded(source())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "cases.json"
            labels_path = root / "labels.json"
            development_path = root / "development.json"
            output = root / "release.json"
            source_path.write_bytes(source_raw)
            labels_path.write_bytes(encoded(labels(source_raw)))
            development_path.write_bytes(DEVELOPMENT)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, corpus.main([
                    "--source", str(source_path),
                    "--labels", str(labels_path),
                    "--development", str(development_path),
                    "--output", str(output),
                ]))
            self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
            self.assertEqual("sealed", json.loads(output.read_bytes())["status"])
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    corpus.main([
                        "--source", str(source_path),
                        "--labels", str(labels_path),
                        "--development", str(development_path),
                        "--output", str(output),
                    ])


if __name__ == "__main__":
    unittest.main()
