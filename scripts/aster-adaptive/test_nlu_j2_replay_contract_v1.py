import copy
import unittest

import nlu_j2_artifact_contract_v1 as artifact
import nlu_j2_replay_contract_v1 as replay
import nlu_whole_label_choice_v1 as ontology
from test_nlu_j2_artifact_contract_v1 import ADMISSION, CORPUS_RELEASE, value


def records():
    labels = sorted(ontology.CATALOGUE)
    rows = []
    for label in range(16):
        for case in range(12):
            rows.append({
                "id": f"j2-validation-l{label:02d}-case-{case:02d}",
                "label_id": labels[label], "confidence": 0.75,
                "margin": 0.5,
                "guarded_interpretation": copy.deepcopy(
                    ontology.CATALOGUE[labels[label]]),
                "accepted": case < 10,
            })
    return rows


def inputs():
    rows = records(); candidate = value()
    candidate["accepted_validation_rows"] = 160
    candidate["validation_replay_sha256"] = replay.records_sha256(rows)
    candidate["artifact_sha256"] = artifact.artifact_sha256(candidate)
    artifact_raw = artifact.canonical(candidate)
    base = {"schema": "aster-nlu-j2-validation-replay.v1",
            "artifact_sha256": candidate["artifact_sha256"],
            "backend": "portable-python-cpu-reference", "cpu_threads": 1,
            "rows": 192, "records": rows, "authority": "none",
            "automatic_routing": "off"}
    first = dict(base, run_id="clean-cpu-1")
    second = dict(base, run_id="clean-cpu-2")
    return artifact_raw, artifact.canonical(first), artifact.canonical(second)


class J2ReplayContractTests(unittest.TestCase):
    def test_two_exact_clean_cpu_replays_validate_without_deployment(self):
        result = replay.validate(*inputs(), CORPUS_RELEASE, ADMISSION)
        self.assertEqual(2, result["clean_cpu_reproductions"])
        self.assertTrue(result["exact_record_equality"])
        self.assertFalse(result["deployment"])

    def test_record_case_acceptance_and_second_run_drift_fail_closed(self):
        artifact_raw, first_raw, second_raw = inputs()
        second = artifact.decode_unique_json(second_raw)
        second["records"][0]["margin"] = 0.4
        with self.assertRaises(ValueError):
            replay.validate(artifact_raw, first_raw, artifact.canonical(second),
                            CORPUS_RELEASE, ADMISSION)
        second = artifact.decode_unique_json(second_raw)
        second["records"][0]["id"] = "unknown"
        with self.assertRaises(ValueError):
            replay.validate(artifact_raw, first_raw, artifact.canonical(second),
                            CORPUS_RELEASE, ADMISSION)
        second = artifact.decode_unique_json(second_raw)
        second["records"][0]["accepted"] = False
        with self.assertRaises(ValueError):
            replay.validate(artifact_raw, first_raw, artifact.canonical(second),
                            CORPUS_RELEASE, ADMISSION)

    def test_duplicate_nonfinite_and_unknown_label_fail_closed(self):
        artifact_raw, first_raw, second_raw = inputs()
        first = artifact.decode_unique_json(first_raw)
        first["records"][0]["label_id"] = "L-unknown"
        with self.assertRaises(ValueError):
            replay.validate(artifact_raw, artifact.canonical(first), second_raw,
                            CORPUS_RELEASE, ADMISSION)
        duplicate = first_raw.replace(b'"rows":192', b'"rows":192,"rows":192')
        with self.assertRaises(ValueError):
            replay.validate(artifact_raw, duplicate, second_raw,
                            CORPUS_RELEASE, ADMISSION)


if __name__ == "__main__": unittest.main()
