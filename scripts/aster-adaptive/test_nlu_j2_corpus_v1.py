import copy
import json
import unittest

import nlu_j2_corpus_v1 as corpus
import nlu_whole_label_choice_v1 as ontology


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def references():
    return {f"reference-{index}": encoded({"cases": [
        {"id": f"r{index}", "text": f"Exposed reference request {index}"}
    ]}) for index in range(corpus.REFERENCE_COUNT)}


def value():
    cases = []
    for label_index, label_id in enumerate(sorted(ontology.CATALOGUE)):
        for split, count in (("train", corpus.TRAIN_PER_LABEL),
                             ("validation", corpus.VALIDATION_PER_LABEL)):
            for index in range(count):
                suffix = f"label-{label_index:02d}-case-{index:02d}"
                cases.append({"id": f"j2-{split}-{suffix}", "split": split,
                              "text": f"Independent J2 {split} request {suffix}",
                              "label_id": label_id})
    return {"schema": corpus.SCHEMA, "manifest_sha256": corpus.MANIFEST_SHA256,
            "data_class": corpus.DATA_CLASS, "evidence_class": corpus.EVIDENCE_CLASS,
            "ontology_sha256": corpus.ontology_sha256(), "custodian": corpus.CUSTODIAN,
            "authority": corpus.AUTHORITY, "cases": cases}


class J2CorpusTests(unittest.TestCase):
    def test_balanced_disjoint_corpus_is_accepted(self):
        summary = corpus.validate_corpus(encoded(value()), references())
        self.assertEqual(960, summary["case_count"])
        self.assertEqual(768, summary["train_count"])
        self.assertEqual(192, summary["validation_count"])
        self.assertEqual(8, len(summary["references"]))
        self.assertEqual(0, summary["overlap_count"])
        self.assertEqual("not-granted", summary["authority"])

    def test_requires_exactly_eight_reference_sets(self):
        refs = references(); refs.pop(next(iter(refs)))
        with self.assertRaisesRegex(ValueError, "eight"):
            corpus.validate_corpus(encoded(value()), refs)

    def test_overlap_duplicate_and_imbalance_fail_closed(self):
        base = value()
        overlap = copy.deepcopy(base)
        overlap["cases"][0]["text"] = "Exposed reference request 0"
        duplicate = copy.deepcopy(base)
        duplicate["cases"][1]["text"] = duplicate["cases"][0]["text"]
        imbalance = copy.deepcopy(base)
        imbalance["cases"][0]["label_id"] = imbalance["cases"][-1]["label_id"]
        for changed in (overlap, duplicate, imbalance):
            with self.subTest(), self.assertRaises(ValueError):
                corpus.validate_corpus(encoded(changed), references())

    def test_metadata_and_unique_json_fail_closed(self):
        changed = value(); changed["authority"] = "granted"
        with self.assertRaises(ValueError):
            corpus.validate_corpus(encoded(changed), references())
        duplicate = encoded(value()).replace(
            b'"authority":"not-granted"',
            b'"authority":"not-granted","authority":"granted"', 1)
        with self.assertRaises(ValueError):
            corpus.validate_corpus(duplicate, references())

    def test_reference_schema_and_normalized_duplicates_fail_closed(self):
        bad = references(); bad["reference-0"] = b"{}\n"
        with self.assertRaises(ValueError):
            corpus.validate_corpus(encoded(value()), bad)
        duplicate = references(); duplicate["reference-0"] = encoded({"cases": [
            {"id": "a", "text": "Same exposed request"},
            {"id": "b", "text": "same   exposed request"}]})
        with self.assertRaises(ValueError):
            corpus.validate_corpus(encoded(value()), duplicate)


if __name__ == "__main__":
    unittest.main()
