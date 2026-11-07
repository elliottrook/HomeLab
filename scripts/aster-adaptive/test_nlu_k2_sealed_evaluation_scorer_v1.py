import hashlib
import json
import unittest
from unittest import mock

import nlu_k2_sealed_evaluation_scorer_v1 as scorer
import nlu_whole_label_choice_v1 as ontology


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def evaluation():
    cases = []
    for index, label_id in enumerate(ontology.CATALOGUE):
        for suffix in ("a", "b"):
            cases.append({"id": f"j2-evaluation-case-{index:02d}-{suffix}",
                          "text": f"synthetic sealed request {index} {suffix}",
                          "label_id": label_id})
    return {
        "schema": "aster-nlu-j2-sealed-evaluation.v1",
        "manifest_sha256": scorer.MANIFEST_SHA256,
        "data_class": "synthetic",
        "evidence_class": "preregistered-sealed-evaluation",
        "ontology_sha256": scorer.ONTOLOGY_SHA256,
        "custodian": "independent-j2-evaluation-custodian",
        "sealed_before_training": True, "trainer_access": "forbidden",
        "authority": "not-granted", "cases": cases,
    }


def records(cases):
    return {"schema": "aster-nlu-k2-sealed-evaluation-records.v1",
            "records": [{"case_id": case["id"], "fixture": case["label_id"]}
                        for case in cases],
            "authority": "not-granted"}


def decision(record):
    return {"case_id": record["case_id"],
            "final_label_id": record["fixture"], "accepted": True}


class K2SealedEvaluationScorerTests(unittest.TestCase):
    def invoke(self, evaluation_value, records_value):
        evaluation_raw = raw(evaluation_value)
        with mock.patch.object(scorer, "EVALUATION_SHA256",
                               hashlib.sha256(evaluation_raw).hexdigest()), \
             mock.patch.object(scorer.policy, "decide", side_effect=decision):
            return json.loads(scorer.score(
                evaluation_raw, raw(records_value), model_requests=32,
                retries=0, response_errors=0))

    def test_exact_sealed_result_passes_content_free(self):
        source = evaluation(); result = self.invoke(source, records(source["cases"]))
        self.assertEqual("pass", result["status"])
        self.assertEqual("aster-nlu-k2-sealed-evaluation-metrics.v1",
                         result["schema"])
        self.assertEqual(32, result["exact"])
        self.assertNotIn("records", result)
        self.assertNotIn("text", result)

    def test_quality_rejection_is_valid_complete_evidence(self):
        source = evaluation(); result_records = records(source["cases"])
        result_records["records"][0]["fixture"] = source["cases"][2]["label_id"]
        result_records["records"][1]["fixture"] = source["cases"][2]["label_id"]
        result = self.invoke(source, result_records)
        self.assertEqual("reject", result["status"])
        self.assertEqual(30, result["exact"])

    def test_counts_or_errors_fail_closed(self):
        source = evaluation(); result_records = records(source["cases"])
        evaluation_raw = raw(source)
        with mock.patch.object(scorer, "EVALUATION_SHA256",
                               hashlib.sha256(evaluation_raw).hexdigest()), \
             mock.patch.object(scorer.policy, "decide", side_effect=decision):
            for values in ((31, 0, 0), (32, 1, 0), (32, 0, 1)):
                with self.assertRaises(ValueError):
                    scorer.score(evaluation_raw, raw(result_records),
                                 model_requests=values[0], retries=values[1],
                                 response_errors=values[2])

    def test_identity_or_duplicate_result_fails_closed(self):
        source = evaluation(); result_records = records(source["cases"])
        result_records["records"][1]["case_id"] = result_records["records"][0]["case_id"]
        with self.assertRaises(ValueError): self.invoke(source, result_records)
        with mock.patch.object(scorer, "EVALUATION_SHA256", "0" * 64):
            with self.assertRaisesRegex(ValueError, "identity"):
                scorer.truth(raw(source))

    def test_reconciliation_requires_matching_restored_terminal(self):
        source = evaluation(); metrics = self.invoke(source, records(source["cases"]))
        metrics_raw = raw(metrics)
        terminal = {
            "schema": "aster-nlu-k2-sealed-evaluation-terminal.v1",
            "state": "complete",
            "booking_id": "aster-stream-a-m3-k2-sealed-20261107-1200-r1",
            "workload_id": "m3-k2-sealed-evaluation-v1",
            "model_requests": 32, "retries": 0, "response_errors": 0,
            "production_restored": True,
            "result_sha256": metrics["result_sha256"],
        }
        final = json.loads(scorer.reconcile(metrics_raw, raw(terminal)))
        self.assertEqual("aster-nlu-k2-sealed-evaluation-score.v1",
                         final["schema"])
        self.assertTrue(final["production_restored"])
        terminal["production_restored"] = False
        with self.assertRaises(ValueError):
            scorer.reconcile(metrics_raw, raw(terminal))


if __name__ == "__main__":
    unittest.main()
