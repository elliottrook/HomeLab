import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))

import nlu_j2_corpus_v1 as corpus_boundary
import nlu_j2_evaluation_v1 as evaluation
import nlu_whole_label_choice_v1 as ontology


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def fixtures():
    corpus_cases = []
    evaluation_cases = []
    counter = 0
    for label in ontology.CATALOGUE:
        for index in range(60):
            corpus_cases.append({
                "id": f"corpus-{counter:04d}",
                "split": "train" if index < 48 else "validation",
                "text": f"corpus request {counter:04d} for {label}",
                "label_id": label,
            })
            counter += 1
        for index in range(2):
            evaluation_cases.append({
                "id": f"j2-evaluation-case-{len(evaluation_cases):03d}",
                "text": f"sealed evaluation request {len(evaluation_cases):03d} for {label}",
                "label_id": label,
            })
    corpus = {"cases": corpus_cases}
    sealed = {
        "schema": evaluation.SCHEMA,
        "manifest_sha256": evaluation.MANIFEST_SHA256,
        "data_class": "synthetic",
        "evidence_class": "preregistered-sealed-evaluation",
        "ontology_sha256": corpus_boundary.ontology_sha256(),
        "custodian": evaluation.CUSTODIAN,
        "sealed_before_training": True,
        "trainer_access": "forbidden",
        "authority": "not-granted",
        "cases": evaluation_cases,
    }
    return corpus, sealed


class EvaluationTests(unittest.TestCase):
    def validate(self, corpus, sealed):
        corpus_raw = raw(corpus)
        corpus_texts = evaluation.normalized_set(corpus, 960)
        with mock.patch.object(evaluation, "CORPUS_SHA256",
                               hashlib.sha256(corpus_raw).hexdigest()), \
                mock.patch.object(evaluation, "CORPUS_SET_SHA256",
                                  evaluation.set_sha256(corpus_texts)):
            return evaluation.validate(raw(sealed), corpus_raw)

    def test_balanced_disjoint_evaluation_passes(self):
        corpus, sealed = fixtures()
        result = self.validate(corpus, sealed)
        self.assertEqual(result["cases"], 32)
        self.assertEqual(result["intersection_count"], 0)
        self.assertEqual(result["trainer_access"], "forbidden")

    def test_overlap_fails_closed(self):
        corpus, sealed = fixtures()
        sealed["cases"][0]["text"] = corpus["cases"][0]["text"]
        with self.assertRaisesRegex(ValueError, "overlaps"):
            self.validate(corpus, sealed)

    def test_unbalanced_labels_fail_closed(self):
        corpus, sealed = fixtures()
        sealed["cases"][0]["label_id"] = sealed["cases"][2]["label_id"]
        with self.assertRaisesRegex(ValueError, "balanced"):
            self.validate(corpus, sealed)

    def test_unsealed_or_trainer_visible_fails_closed(self):
        corpus, sealed = fixtures()
        for field, changed in (("sealed_before_training", False),
                               ("trainer_access", "allowed")):
            candidate = json.loads(json.dumps(sealed))
            candidate[field] = changed
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "metadata"):
                self.validate(corpus, candidate)


if __name__ == "__main__":
    unittest.main()
