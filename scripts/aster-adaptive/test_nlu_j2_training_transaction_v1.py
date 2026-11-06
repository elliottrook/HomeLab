import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import nlu_j2_artifact_contract_v1 as artifact
import nlu_j2_corpus_v1 as corpus_contract
import nlu_j2_reference_forward_v1 as forward
import nlu_j2_training_admission_v1 as admission
import nlu_j2_training_transaction_v1 as transaction


RECIPE = Path(__file__).parent / "fixtures" / "nlu-j2-training-recipe-manifest-v1.json"


def fixture():
    cases = []
    for label_index, label_id in enumerate(forward.LABELS):
        for case in range(48):
            cases.append({
                "id": f"j2-train-l{label_index:02d}-case-{case:02d}",
                "split": "train", "text": f"train {label_index} {case}",
                "label_id": label_id,
            })
        for case in range(48, 60):
            cases.append({
                "id": f"j2-validation-l{label_index:02d}-case-{case:02d}",
                "split": "validation",
                "text": f"validation {label_index} {case}",
                "label_id": label_id,
            })
    corpus_raw = artifact.canonical({
        "schema": corpus_contract.SCHEMA,
        "manifest_sha256": corpus_contract.MANIFEST_SHA256,
        "data_class": corpus_contract.DATA_CLASS,
        "evidence_class": corpus_contract.EVIDENCE_CLASS,
        "ontology_sha256": corpus_contract.ontology_sha256(),
        "custodian": corpus_contract.CUSTODIAN,
        "authority": "not-granted", "cases": cases,
    })
    release_raw = artifact.canonical({
        "schema": "aster-nlu-j2-corpus-release-summary.v1",
        "corpus_sha256": hashlib.sha256(corpus_raw).hexdigest(),
        "training_authorized": False, "authority": "not-granted",
        "automatic_routing": "off",
    })
    admission_raw = admission.canonical(admission.EXPECTED_RESULT)
    truth_raw = artifact.canonical({
        "schema": "aster-nlu-j2-validation-truth.v1",
        "rows": [{"id": row["id"], "text": row["text"],
                  "label_id": row["label_id"]}
                 for row in sorted(cases, key=lambda row: row["id"])
                 if row["split"] == "validation"],
        "authority": "none", "automatic_routing": "off",
    })
    return corpus_raw, release_raw, admission_raw, truth_raw


class J2TrainingTransactionTests(unittest.TestCase):
    def test_audit_and_create_only_writer_fail_closed(self):
        with self.assertRaises(RuntimeError):
            transaction._audit("socket.connect", ())
        transaction._audit("open", ())
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "value"
            transaction._write_exclusive(path, b"one")
            self.assertEqual(b"one", path.read_bytes())
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            with self.assertRaises(FileExistsError):
                transaction._write_exclusive(path, b"two")

    def test_exact_inputs_produce_frozen_split_without_evaluation_access(self):
        corpus_raw, release_raw, admission_raw, truth_raw = fixture()
        with patch.object(transaction, "CORPUS_SHA256",
                          hashlib.sha256(corpus_raw).hexdigest()), \
                patch.object(transaction, "CORPUS_RELEASE_SHA256",
                             hashlib.sha256(release_raw).hexdigest()), \
                patch.object(transaction, "VALIDATION_TRUTH_SHA256",
                             hashlib.sha256(truth_raw).hexdigest()):
            result = transaction._load_inputs(
                corpus_raw, release_raw, admission_raw, RECIPE.read_bytes())
        self.assertEqual(768, len(result["train_rows"]))
        self.assertEqual(192, len(result["validation_rows"]))
        self.assertEqual(truth_raw, result["validation_truth_raw"])
        self.assertEqual(
            hashlib.sha256(admission_raw).hexdigest(),
            result["training_admission_sha256"])

    def test_input_identity_row_and_truth_drift_fail_closed(self):
        corpus_raw, release_raw, admission_raw, truth_raw = fixture()
        with self.assertRaisesRegex(ValueError, "identity changed"):
            transaction._load_inputs(
                corpus_raw, release_raw, admission_raw, RECIPE.read_bytes())
        changed = admission.canonical(dict(admission.EXPECTED_RESULT,
                                           training_authorized=True))
        with self.assertRaises(ValueError):
            admission.validate_result(changed)

        value = transaction.decode_unique_json(corpus_raw)
        value["cases"][0]["id"] = value["cases"][1]["id"]
        changed_corpus = artifact.canonical(value)
        changed_release = artifact.canonical({
            "schema": "aster-nlu-j2-corpus-release-summary.v1",
            "corpus_sha256": hashlib.sha256(changed_corpus).hexdigest(),
            "training_authorized": False, "authority": "not-granted",
            "automatic_routing": "off",
        })
        with patch.object(transaction, "CORPUS_SHA256",
                          hashlib.sha256(changed_corpus).hexdigest()), \
                patch.object(transaction, "CORPUS_RELEASE_SHA256",
                             hashlib.sha256(changed_release).hexdigest()), \
                self.assertRaisesRegex(ValueError, "row changed"):
            transaction._load_inputs(
                changed_corpus, changed_release, admission_raw,
                RECIPE.read_bytes())

    def test_epoch_summary_and_quantization_are_bounded(self):
        labels = forward.LABELS
        rows = [{"id": f"row-{index}", "text": "x",
                 "label_id": labels[0]} for index in range(192)]
        predicted = {"label_id": labels[0], "probabilities":
                     [1.0] + [0.0] * 15}
        with patch.object(transaction.forward, "forward",
                          return_value=predicted), \
                patch.object(transaction, "_guarded_exact", return_value=True):
            summary = transaction._validate_epoch(1, rows, {})
        self.assertEqual(192, summary["raw_exact_count"])
        self.assertEqual(192, summary["guarded_exact_count"])
        self.assertEqual(0.0, summary["mean_validation_loss"])

        tensors = transaction._initial_tensors()
        quantized = transaction._quantized(tensors)
        self.assertEqual(set(tensors), set(quantized))
        self.assertTrue(all(round(value, 10) == value
                            for values in quantized.values()
                            for value in values))

    def test_execute_retains_bounded_failure_without_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = []
            for name in ("corpus", "release", "admission", "recipe"):
                path = root / name; path.write_bytes(b"x"); paths.append(path)
            output = root / "retained"
            with patch.object(transaction, "_run",
                              side_effect=RuntimeError("private detail")), \
                    self.assertRaises(RuntimeError):
                transaction.execute(*paths, output)
            failure = json.loads((output / "failure.json").read_bytes())
            self.assertEqual("training-worker", failure["first_failure_phase"])
            self.assertEqual("RuntimeError", failure["failure_class"])
            self.assertFalse(failure["production_changed"])
            self.assertFalse(failure["sealed_evaluation_access"])
            self.assertNotIn("private detail", json.dumps(failure))
            with self.assertRaisesRegex(ValueError, "already exists"):
                transaction.execute(*paths, output)


if __name__ == "__main__": unittest.main()
