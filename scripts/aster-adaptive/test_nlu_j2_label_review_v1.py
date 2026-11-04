import copy
import json
import unittest

import nlu_j2_corpus_v1 as corpus
import nlu_j2_label_review_v1 as review
import nlu_whole_label_choice_v1 as ontology


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def source():
    cases = []
    for label_index, label_id in enumerate(sorted(ontology.CATALOGUE)):
        for split, count in (("train", 48), ("validation", 12)):
            for index in range(count):
                cases.append({
                    "id": f"j2-{split}-label-{label_index:02d}-case-{index:02d}",
                    "split": split,
                    "text": f"Synthetic J2 request {label_index} {split} {index}",
                    "label_id": label_id,
                })
    return {
        "schema": corpus.SCHEMA,
        "manifest_sha256": corpus.MANIFEST_SHA256,
        "data_class": corpus.DATA_CLASS,
        "evidence_class": corpus.EVIDENCE_CLASS,
        "ontology_sha256": corpus.ontology_sha256(),
        "custodian": corpus.CUSTODIAN,
        "authority": corpus.AUTHORITY,
        "cases": cases,
    }


def complete():
    raw = encoded(source())
    value = review.template(raw)
    labels = {case["id"]: case["label_id"] for case in source()["cases"]}
    for row in value["rows"]:
        row.update(status="accepted", reviewed_label_id=labels[row["id"]])
    value["review_sha256"] = review.review_sha256(value)
    return raw, value


class J2LabelReviewTests(unittest.TestCase):
    def test_complete_review_is_release_eligible(self):
        raw, value = complete()
        summary = review.validate(raw, encoded(value))
        self.assertEqual(960, summary["accepted"])
        self.assertEqual(0, summary["corrected"])
        self.assertTrue(summary["release_eligible"])

    def test_correction_is_valid_but_not_release_eligible(self):
        raw, value = complete()
        original = value["rows"][0]["reviewed_label_id"]
        replacement = next(item for item in sorted(ontology.CATALOGUE)
                           if item != original)
        value["rows"][0].update(status="corrected", reviewed_label_id=replacement)
        value["review_sha256"] = review.review_sha256(value)
        summary = review.validate(raw, encoded(value))
        self.assertEqual(1, summary["corrected"])
        self.assertFalse(summary["release_eligible"])

    def test_pending_duplicate_identity_authority_and_hash_fail(self):
        raw, valid = complete()
        variants = []
        pending = copy.deepcopy(valid); pending["rows"][0]["status"] = "pending"
        pending["review_sha256"] = review.review_sha256(pending); variants.append(pending)
        duplicate = copy.deepcopy(valid); duplicate["rows"][1]["id"] = duplicate["rows"][0]["id"]
        duplicate["review_sha256"] = review.review_sha256(duplicate); variants.append(duplicate)
        same_role = copy.deepcopy(valid); same_role["reviewer_id"] = corpus.CUSTODIAN
        same_role["review_sha256"] = review.review_sha256(same_role); variants.append(same_role)
        authority = copy.deepcopy(valid); authority["authority"] = "granted"
        authority["review_sha256"] = review.review_sha256(authority); variants.append(authority)
        bad_hash = copy.deepcopy(valid); bad_hash["review_sha256"] = "0" * 64
        variants.append(bad_hash)
        for value in variants:
            with self.subTest(), self.assertRaises(ValueError):
                review.validate(raw, encoded(value))

    def test_source_identity_and_count_fail_closed(self):
        raw, value = complete()
        changed = source(); changed["manifest_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            review.validate(encoded(changed), encoded(value))
        short = source(); short["cases"].pop()
        with self.assertRaises(ValueError):
            review.template(encoded(short))


if __name__ == "__main__":
    unittest.main()
