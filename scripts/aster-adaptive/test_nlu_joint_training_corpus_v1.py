import copy
import json
import unittest

import nlu_joint_training_corpus_v1 as corpus
import nlu_whole_label_choice_v1 as ontology


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def reference(text="reference request"):
    return encoded({"schema": "fixture.v1", "cases": [{"id": "r1", "text": text}]})


def value():
    cases = []
    for label_index, label_id in enumerate(sorted(ontology.CATALOGUE)):
        for split, count in (("train", corpus.TRAIN_PER_LABEL),
                             ("validation", corpus.VALIDATION_PER_LABEL)):
            for index in range(count):
                suffix = f"label-{label_index:02d}-case-{index:02d}"
                cases.append({
                    "id": f"j1-{split}-{suffix}",
                    "split": split,
                    "text": f"Synthetic {split} request {suffix}",
                    "label_id": label_id,
                })
    return {
        "schema": corpus.SCHEMA,
        "data_class": corpus.DATA_CLASS,
        "evidence_class": corpus.EVIDENCE_CLASS,
        "ontology_sha256": corpus.ontology_sha256(),
        "authority": corpus.AUTHORITY,
        "cases": cases,
    }


class J1CorpusTests(unittest.TestCase):
    def test_balanced_disjoint_corpus_is_accepted(self):
        summary = corpus.validate_corpus(encoded(value()), {"public": reference()})
        self.assertEqual(400, summary["case_count"])
        self.assertEqual(320, summary["train_count"])
        self.assertEqual(80, summary["validation_count"])
        self.assertEqual(16, summary["label_count"])
        self.assertEqual(0, summary["overlap_count"])
        self.assertEqual("not-granted", summary["authority"])

    def test_overlap_duplicate_and_unbalanced_corpora_fail(self):
        base = value()
        changes = []
        overlap = copy.deepcopy(base)
        overlap["cases"][0]["text"] = "Reference request"
        changes.append(overlap)
        duplicate = copy.deepcopy(base)
        duplicate["cases"][1]["text"] = duplicate["cases"][0]["text"]
        changes.append(duplicate)
        unbalanced = copy.deepcopy(base)
        unbalanced["cases"][0]["label_id"] = unbalanced["cases"][-1]["label_id"]
        changes.append(unbalanced)
        for item in changes:
            with self.subTest(), self.assertRaises(ValueError):
                corpus.validate_corpus(encoded(item), {"public": reference()})

    def test_metadata_and_unique_json_fail_closed(self):
        changed = value()
        changed["authority"] = "granted"
        with self.assertRaises(ValueError):
            corpus.validate_corpus(encoded(changed), {"public": reference()})
        duplicate = encoded(value()).replace(
            b'"authority":"not-granted"',
            b'"authority":"not-granted","authority":"granted"',
            1,
        )
        with self.assertRaises(ValueError):
            corpus.validate_corpus(duplicate, {"public": reference()})

    def test_reference_drift_and_duplicate_reference_fail(self):
        with self.assertRaises(ValueError):
            corpus.validate_corpus(encoded(value()), {"public": b"{}\n"})
        duplicate_reference = encoded({
            "cases": [
                {"id": "a", "text": "Same request"},
                {"id": "b", "text": "same request"},
            ]
        })
        with self.assertRaises(ValueError):
            corpus.validate_corpus(encoded(value()), {"public": duplicate_reference})


if __name__ == "__main__":
    unittest.main()
