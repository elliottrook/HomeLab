import contextlib
import io
import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import nlu_calibration_corpus_v4 as corpus
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
                "id": f"cal-v4-{family}-{number:02d}",
                "family": family,
                "text": f"Fresh synthetic v4 request {family} number {number}",
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
    rows = []
    for case in json.loads(source_raw)["cases"]:
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


def manifest(source_raw):
    return {
        "schema": corpus.MANIFEST_SCHEMA,
        "release_id": corpus.RELEASE_ID,
        "custodian_role": corpus.CASE_CUSTODIAN,
        "case_count": 60,
        "files": {
            "cases.json": {"bytes": len(source_raw), "sha256": sha256(source_raw)},
            "custodian-design.json": {"bytes": 123, "sha256": "a" * 64},
        },
        "authority": "not-granted",
    }


def normalized_set_sha256(source_value):
    texts = sorted(corpus.base.normalized_text(case["text"]) for case in source_value["cases"])
    return sha256(("\n".join(texts) + "\n").encode())


class CalibrationV4CorpusTests(unittest.TestCase):
    def bindings(self, source_raw, label_raw, manifest_raw):
        return mock.patch.multiple(
            corpus,
            EXPECTED_SOURCE_SHA256=sha256(source_raw),
            EXPECTED_LABEL_SHA256=sha256(label_raw),
            EXPECTED_MANIFEST_SHA256=sha256(manifest_raw),
            EXPECTED_DEVELOPMENT_SHA256=sha256(DEVELOPMENT),
            EXPECTED_NORMALIZED_TEXT_SET_SHA256=normalized_set_sha256(json.loads(source_raw)),
        )

    def test_builds_exact_balanced_content_free_v4_release(self):
        source_raw = encoded(source())
        label_raw = encoded(labels(source_raw))
        manifest_raw = encoded(manifest(source_raw))
        with self.bindings(source_raw, label_raw, manifest_raw):
            release, summary = corpus.build_release(
                source_raw, label_raw, manifest_raw, DEVELOPMENT
            )
        self.assertEqual(corpus.RELEASE_ID, release["release_id"])
        self.assertEqual(corpus.CANDIDATE_SHA256, release["candidate_bundle_sha256"])
        self.assertEqual(60, summary["case_count"])
        self.assertEqual({family: 10 for family in FAMILIES}, summary["family_counts"])
        self.assertEqual({
            "case_custodian": corpus.CASE_CUSTODIAN,
            "label_reviewer": corpus.LABEL_REVIEWER,
            "scoring_operator": corpus.SCORING_OPERATOR,
        }, release["roles"])
        self.assertTrue(all(set(row) == {
            "id", "family", "case_sha256", "label_sha256", "review_receipt_sha256",
        } for row in release["cases"]))

    def test_every_exact_digest_binding_fails_closed(self):
        source_raw = encoded(source())
        label_raw = encoded(labels(source_raw))
        manifest_raw = encoded(manifest(source_raw))
        with self.bindings(source_raw, label_raw, manifest_raw):
            checks = (
                ("EXPECTED_SOURCE_SHA256", "source SHA-256 changed"),
                ("EXPECTED_LABEL_SHA256", "labels SHA-256 changed"),
                ("EXPECTED_MANIFEST_SHA256", "manifest SHA-256 changed"),
                ("EXPECTED_DEVELOPMENT_SHA256", "development fixture SHA-256 changed"),
                ("EXPECTED_NORMALIZED_TEXT_SET_SHA256", "text-set SHA-256 changed"),
            )
            for name, message in checks:
                with self.subTest(name=name), mock.patch.object(corpus, name, "0" * 64):
                    with self.assertRaisesRegex(ValueError, message):
                        corpus.build_release(source_raw, label_raw, manifest_raw, DEVELOPMENT)

    def test_manifest_role_label_family_and_content_boundaries_fail_closed(self):
        source_raw = encoded(source())
        label_raw = encoded(labels(source_raw))
        manifest_value = manifest(source_raw)
        manifest_value["custodian_role"] = corpus.SCORING_OPERATOR
        manifest_raw = encoded(manifest_value)
        with self.bindings(source_raw, label_raw, manifest_raw):
            with self.assertRaisesRegex(ValueError, "manifest role changed"):
                corpus.build_release(source_raw, label_raw, manifest_raw, DEVELOPMENT)

        manifest_raw = encoded(manifest(source_raw))
        labels_value = labels(source_raw)
        labels_value["reviewer"] = corpus.CASE_CUSTODIAN
        changed_labels = encoded(labels_value)
        with self.bindings(source_raw, changed_labels, manifest_raw):
            with self.assertRaisesRegex(ValueError, "independent reviewer"):
                corpus.build_release(source_raw, changed_labels, manifest_raw, DEVELOPMENT)

        labels_value = labels(source_raw)
        labels_value["labels"][0]["label"]["text"] = "forbidden"
        changed_labels = encoded(labels_value)
        with self.bindings(source_raw, changed_labels, manifest_raw):
            with self.assertRaisesRegex(ValueError, "dimensions"):
                corpus.build_release(source_raw, changed_labels, manifest_raw, DEVELOPMENT)

        labels_value = labels(source_raw)
        labels_value["labels"][0]["label"]["request_family"] = "general-answer"
        changed_labels = encoded(labels_value)
        with self.bindings(source_raw, changed_labels, manifest_raw):
            with self.assertRaisesRegex(ValueError, "family does not match"):
                corpus.build_release(source_raw, changed_labels, manifest_raw, DEVELOPMENT)

    def test_cli_writes_owner_only_and_refuses_overwrite(self):
        source_raw = encoded(source())
        label_raw = encoded(labels(source_raw))
        manifest_raw = encoded(manifest(source_raw))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "cases.json"
            labels_path = root / "labels.json"
            manifest_path = root / "manifest.json"
            development_path = root / "development.json"
            output = root / "release.json"
            source_path.write_bytes(source_raw)
            labels_path.write_bytes(label_raw)
            manifest_path.write_bytes(manifest_raw)
            development_path.write_bytes(DEVELOPMENT)
            arguments = [
                "--source", str(source_path),
                "--labels", str(labels_path),
                "--manifest", str(manifest_path),
                "--development", str(development_path),
                "--output", str(output),
            ]
            with self.bindings(source_raw, label_raw, manifest_raw):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(0, corpus.main(arguments))
                self.assertEqual(0o600, stat.S_IMODE(output.stat().st_mode))
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        corpus.main(arguments)


if __name__ == "__main__":
    unittest.main()
