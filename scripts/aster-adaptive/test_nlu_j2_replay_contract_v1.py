import copy
import hashlib
import unittest

import nlu_j2_artifact_contract_v1 as artifact
import nlu_j2_replay_contract_v1 as replay
import nlu_whole_label_choice_v1 as ontology
from test_nlu_j2_artifact_contract_v1 import ADMISSION, CORPUS_RELEASE, value


LABELS = sorted(ontology.CATALOGUE)


def truth_value():
    return {"schema": "aster-nlu-j2-validation-truth.v1",
            "rows": [{"id": f"j2-validation-l{label:02d}-case-{case:02d}",
                      "text": f"synthetic label {label} case {case}",
                      "label_id": LABELS[label]}
                     for label in range(16) for case in range(48, 60)],
            "authority": "none", "automatic_routing": "off"}


def forward(text, _tensors):
    words = text.split(); label = int(words[2]); case = int(words[4])
    selected = label if case - 48 < 10 else (label + 1) % 16
    return {"label_id": LABELS[selected],
            "confidence": 0.75 if case - 48 < 10 else 0.55,
            "margin": 0.5 if case - 48 < 10 else 0.1,
            "probabilities": []}


def epoch_summaries():
    return [{"epoch": epoch, "rows": 192, "raw_exact_count": 160,
             "guarded_exact_count": 160,
             "mean_validation_loss": round(1.0 / epoch, 12)}
            for epoch in range(1, 41)]


def inputs():
    candidate = value(); candidate["selected_epoch"] = 40
    candidate["threshold"] = 0.105
    candidate["accepted_validation_rows"] = 160
    truth_raw = artifact.canonical(truth_value())
    expected, threshold_records = replay._recomputed_records(
        truth_value()["rows"], candidate["tensors"], candidate["threshold"], forward)
    tensors_sha = hashlib.sha256(
        artifact.canonical(candidate["tensors"])).hexdigest()
    selection = {
        "schema": "aster-nlu-j2-validation-selection.v1",
        "validation_truth_sha256": hashlib.sha256(truth_raw).hexdigest(),
        "checkpoint_tensors_sha256": tensors_sha,
        "selected_epoch": 40, "epoch_summaries": epoch_summaries(),
        "threshold_records_sha256": replay.records_sha256(threshold_records),
        "threshold": 0.105, "accepted_validation_rows": 160,
        "validation_rows": 192, "minimum_accepted": 116,
        "all_accepted_raw_and_guarded_exact": True,
        "authority": "none", "automatic_routing": "off"}
    selection_raw = artifact.canonical(selection)
    candidate["validation_truth_sha256"] = hashlib.sha256(truth_raw).hexdigest()
    candidate["validation_selection_sha256"] = hashlib.sha256(selection_raw).hexdigest()
    candidate["validation_replay_sha256"] = replay.records_sha256(expected)
    candidate["artifact_sha256"] = artifact.artifact_sha256(candidate)
    artifact_raw = artifact.canonical(candidate)
    base = {"schema": "aster-nlu-j2-validation-replay.v1",
            "artifact_sha256": candidate["artifact_sha256"],
            "backend": "portable-python-cpu-reference", "cpu_threads": 1,
            "rows": 192, "records": expected, "authority": "none",
            "automatic_routing": "off"}
    first = dict(base, run_id="clean-cpu-1")
    second = dict(base, run_id="clean-cpu-2")
    return (artifact_raw, artifact.canonical(first), artifact.canonical(second),
            truth_raw, selection_raw)


def validate(values):
    artifact_raw, first_raw, second_raw, truth_raw, selection_raw = values
    return replay.validate(artifact_raw, first_raw, second_raw,
                           CORPUS_RELEASE, ADMISSION, truth_raw, selection_raw,
                           forward_fn=forward)


class J2ReplayContractTests(unittest.TestCase):
    def test_two_replays_are_recomputed_from_bound_truth_and_selection(self):
        result = validate(inputs())
        self.assertEqual(2, result["clean_cpu_reproductions"])
        self.assertTrue(result["exact_record_equality"])
        self.assertTrue(result["recomputed_from_validation_truth"])
        self.assertEqual(160, result["accepted"])
        self.assertFalse(result["deployment"])

    def test_replay_drift_fails_even_when_both_runs_are_identically_wrong(self):
        artifact_raw, first_raw, second_raw, truth_raw, selection_raw = inputs()
        first = artifact.decode_unique_json(first_raw)
        second = artifact.decode_unique_json(second_raw)
        first["records"][0]["label_id"] = LABELS[1]
        second["records"][0]["label_id"] = LABELS[1]
        with self.assertRaisesRegex(ValueError, "recomputed validation truth"):
            validate((artifact_raw, artifact.canonical(first),
                      artifact.canonical(second), truth_raw, selection_raw))

    def test_truth_and_selection_receipt_tampering_fail_closed(self):
        artifact_raw, first_raw, second_raw, truth_raw, selection_raw = inputs()
        truth = artifact.decode_unique_json(truth_raw)
        truth["rows"][0]["label_id"] = LABELS[1]
        with self.assertRaises(ValueError):
            validate((artifact_raw, first_raw, second_raw,
                      artifact.canonical(truth), selection_raw))
        receipt = artifact.decode_unique_json(selection_raw)
        receipt["threshold"] = 0.11
        with self.assertRaises(ValueError):
            validate((artifact_raw, first_raw, second_raw, truth_raw,
                      artifact.canonical(receipt)))
        receipt = artifact.decode_unique_json(selection_raw)
        receipt["selected_epoch"] = 39
        with self.assertRaises(ValueError):
            validate((artifact_raw, first_raw, second_raw, truth_raw,
                      artifact.canonical(receipt)))

    def test_forward_result_changes_are_detected(self):
        values = inputs()
        artifact_raw, first_raw, second_raw, truth_raw, selection_raw = values
        def changed_forward(text, tensors):
            result = forward(text, tensors)
            if text.endswith("case 48"):
                result = dict(result, margin=0.4)
            return result
        with self.assertRaises(ValueError):
            replay.validate(artifact_raw, first_raw, second_raw,
                            CORPUS_RELEASE, ADMISSION, truth_raw, selection_raw,
                            forward_fn=changed_forward)

    def test_duplicate_unknown_and_nonfinite_fail_closed(self):
        artifact_raw, first_raw, second_raw, truth_raw, selection_raw = inputs()
        duplicate = truth_raw.replace(b'"authority":"none"',
                                      b'"authority":"none","authority":"none"')
        with self.assertRaises(ValueError):
            validate((artifact_raw, first_raw, second_raw, duplicate, selection_raw))
        first = artifact.decode_unique_json(first_raw)
        first["records"][0]["id"] = "unknown"
        with self.assertRaises(ValueError):
            validate((artifact_raw, artifact.canonical(first), second_raw,
                      truth_raw, selection_raw))


if __name__ == "__main__": unittest.main()
