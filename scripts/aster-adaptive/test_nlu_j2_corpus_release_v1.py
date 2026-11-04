import copy
import json
import unittest

import nlu_j2_corpus_release_v1 as release
import nlu_j2_corpus_v1 as corpus
import nlu_j2_custody_receipt_v1 as custody
import nlu_j2_label_review_v1 as review
import nlu_j2_quality_review_v1 as quality
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
                    "text": f"J2 release fixture {label_index} {split} {index}",
                    "label_id": label_id,
                })
    return encoded({
        "schema": corpus.SCHEMA,
        "manifest_sha256": corpus.MANIFEST_SHA256,
        "data_class": corpus.DATA_CLASS,
        "evidence_class": corpus.EVIDENCE_CLASS,
        "ontology_sha256": corpus.ontology_sha256(),
        "custodian": corpus.CUSTODIAN,
        "authority": corpus.AUTHORITY,
        "cases": cases,
    })


def completed_review(source_raw):
    value = review.template(source_raw)
    labels = {case["id"]: case["label_id"]
              for case in json.loads(source_raw)["cases"]}
    for row in value["rows"]:
        row.update(status="accepted", reviewed_label_id=labels[row["id"]])
    value["review_sha256"] = review.review_sha256(value)
    return encoded(value)


def completed_quality(source_raw):
    value = quality.template(source_raw)
    for row in value["rows"]:
        row["judgments"] = {dimension: True for dimension in quality.DIMENSIONS}
    value["review_sha256"] = quality.review_sha256(value)
    return encoded(value)


def corpus_receipt(source_raw, review_raw, quality_raw=None):
    quality_raw = quality_raw or completed_quality(source_raw)
    value = {
        "schema": "aster-nlu-j2-corpus-custody.v1",
        "manifest_sha256": custody.MANIFEST_SHA256,
        "custodian_id": corpus.CUSTODIAN,
        "reviewer_id": review.REVIEWER,
        "corpus_sha256": release.sha256(source_raw),
        "normalized_text_set_sha256": release._normalized_set_sha256(source_raw),
        "label_review_sha256": release.sha256(review_raw),
        "quality_review_sha256": release.sha256(quality_raw),
        "train_rows": 768, "validation_rows": 192, "labels": 16,
        "overlap_reference_count": 8, "normalized_overlap": 0,
        "content_in_receipt": False, "authority": "not-granted",
    }
    value["receipt_sha256"] = custody._digest(value)
    return custody.canonical(value)


class J2CorpusReleaseTests(unittest.TestCase):
    def test_exact_cross_bound_release_is_candidate_only(self):
        source_raw = source()
        review_raw = completed_review(source_raw)
        quality_raw = completed_quality(source_raw)
        summary = release.release(
            source_raw, review_raw, quality_raw,
            corpus_receipt(source_raw, review_raw, quality_raw))
        self.assertTrue(summary["corpus_release_eligible"])
        self.assertFalse(summary["training_authorized"])
        self.assertEqual("not-granted", summary["authority"])

    def test_corpus_review_and_normalized_set_must_cross_bind(self):
        source_raw = source()
        review_raw = completed_review(source_raw)
        quality_raw = completed_quality(source_raw)
        valid = json.loads(corpus_receipt(source_raw, review_raw, quality_raw))
        for field, changed in (
                ("corpus_sha256", "a" * 64),
                ("normalized_text_set_sha256", "b" * 64),
                ("label_review_sha256", "c" * 64),
                ("quality_review_sha256", "d" * 64)):
            value = copy.deepcopy(valid)
            value[field] = changed
            value.pop("receipt_sha256")
            value["receipt_sha256"] = custody._digest(value)
            with self.subTest(field=field), self.assertRaises(ValueError):
                release.release(source_raw, review_raw, quality_raw,
                                custody.canonical(value))

    def test_correction_and_role_substitution_fail_closed(self):
        source_raw = source()
        review_value = json.loads(completed_review(source_raw))
        original = review_value["rows"][0]["reviewed_label_id"]
        replacement = next(item for item in ontology.CATALOGUE if item != original)
        review_value["rows"][0].update(
            status="corrected", reviewed_label_id=replacement)
        review_value["review_sha256"] = review.review_sha256(review_value)
        corrected_raw = encoded(review_value)
        quality_raw = completed_quality(source_raw)
        with self.assertRaisesRegex(ValueError, "release eligible"):
            release.release(source_raw, corrected_raw, quality_raw,
                            corpus_receipt(source_raw, corrected_raw, quality_raw))

        valid_review = completed_review(source_raw)
        receipt = json.loads(corpus_receipt(source_raw, valid_review, quality_raw))
        receipt["reviewer_id"] = "substitute-reviewer"
        receipt.pop("receipt_sha256")
        receipt["receipt_sha256"] = custody._digest(receipt)
        with self.assertRaisesRegex(ValueError, "release eligible"):
            release.release(source_raw, valid_review, quality_raw,
                            custody.canonical(receipt))

    def test_quality_failure_blocks_release(self):
        source_raw = source()
        review_raw = completed_review(source_raw)
        quality_value = json.loads(completed_quality(source_raw))
        quality_value["rows"][0]["judgments"]["grammar"] = False
        quality_value["rows"][0]["notes"] = "Grammar defect."
        quality_value["review_sha256"] = quality.review_sha256(quality_value)
        quality_raw = encoded(quality_value)
        with self.assertRaisesRegex(ValueError, "release eligible"):
            release.release(source_raw, review_raw, quality_raw,
                            corpus_receipt(source_raw, review_raw, quality_raw))

    def test_custody_requires_exactly_eight_references(self):
        source_raw = source()
        review_raw = completed_review(source_raw)
        quality_raw = completed_quality(source_raw)
        receipt = json.loads(corpus_receipt(source_raw, review_raw, quality_raw))
        receipt["overlap_reference_count"] = 9
        receipt.pop("receipt_sha256")
        receipt["receipt_sha256"] = custody._digest(receipt)
        with self.assertRaises(ValueError):
            release.release(source_raw, review_raw, quality_raw,
                            custody.canonical(receipt))


if __name__ == "__main__":
    unittest.main()
