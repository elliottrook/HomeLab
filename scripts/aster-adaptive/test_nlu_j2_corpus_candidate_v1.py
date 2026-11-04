import contextlib
import io
import json
import unittest
from collections import Counter
from unittest import mock

import nlu_j2_corpus_candidate_v1 as candidate
import nlu_j2_corpus_v1 as boundary
import nlu_whole_label_choice_v1 as ontology


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def references():
    return {name: encoded({"cases": [{
        "id": f"reference-{index}",
        "text": f"Distinct exposed reference sentence number {index}.",
    }]}) for index, name in enumerate(candidate.REFERENCE_ARGUMENTS)}


def inventory(refs):
    return {name: boundary._reference(name, raw)[1]
            for name, raw in refs.items()}


def build(refs):
    # Synthetic unit fixtures exercise candidate construction while the
    # unpatched production path remains bound to the exact frozen inventory.
    with mock.patch.object(boundary, "REFERENCE_INVENTORY", inventory(refs)):
        return candidate.build_corpus(refs)


class J2CorpusCandidateTests(unittest.TestCase):
    def test_build_is_deterministic_balanced_and_boundary_validated(self):
        raw_a, summary_a = build(references())
        raw_b, summary_b = build(references())
        self.assertEqual(raw_a, raw_b)
        self.assertEqual(summary_a, summary_b)
        self.assertEqual(960, summary_a["case_count"])
        self.assertEqual(768, summary_a["train_count"])
        self.assertEqual(192, summary_a["validation_count"])
        self.assertEqual(0, summary_a["overlap_count"])

        value = json.loads(raw_a)
        counts = Counter((case["split"], case["label_id"])
                         for case in value["cases"])
        self.assertEqual(set(ontology.CATALOGUE),
                         {case["label_id"] for case in value["cases"]})
        for label_id in ontology.CATALOGUE:
            self.assertEqual(48, counts[("train", label_id)])
            self.assertEqual(12, counts[("validation", label_id)])
        normalized = [boundary.normalized_text(case["text"])
                      for case in value["cases"]]
        self.assertEqual(960, len(set(normalized)))

    def test_validation_subjects_are_held_out_from_training(self):
        raw, _ = build(references())
        value = json.loads(raw)
        for label_index, (_label, subjects, _templates) in enumerate(candidate.SPECS):
            prefix = f"l{label_index:02d}-"
            train = [case["text"] for case in value["cases"]
                     if case["split"] == "train" and prefix in case["id"]]
            validation = [case["text"] for case in value["cases"]
                          if case["split"] == "validation" and prefix in case["id"]]
            self.assertTrue(all(subject not in " ".join(train)
                                for subject in subjects[8:]))
            self.assertTrue(all(subject not in " ".join(validation)
                                for subject in subjects[:8]))

    def test_exact_named_reference_set_is_required(self):
        missing = references()
        missing.pop("calibration-v6")
        with self.assertRaisesRegex(ValueError, "eight named"):
            candidate.build_corpus(missing)
        extra = references()
        extra["ninth"] = encoded({"cases": [{"id": "x", "text": "Ninth text"}]})
        with self.assertRaisesRegex(ValueError, "eight named"):
            candidate.build_corpus(extra)
        renamed = references()
        renamed["calibration-six"] = renamed.pop("calibration-v6")
        with self.assertRaisesRegex(ValueError, "eight named"):
            candidate.build_corpus(renamed)

    def test_production_inventory_rejects_synthetic_reference_bytes(self):
        with self.assertRaisesRegex(ValueError, "pinned"):
            candidate.build_corpus(references())

    def test_candidate_overlap_is_rejected_by_frozen_validator(self):
        raw, _ = build(references())
        first_text = json.loads(raw)["cases"][0]["text"]
        overlap = references()
        overlap["development-v1"] = encoded({"cases": [{
            "id": "overlap", "text": first_text,
        }]})
        with self.assertRaisesRegex(ValueError, "overlaps"):
            build(overlap)

    def test_cli_requires_all_eight_explicit_paths(self):
        parser = candidate._parser()
        args = []
        for name in candidate.REFERENCE_ARGUMENTS:
            args.extend((f"--{name}", f"/{name}.json"))
        args.extend(("--output", "/private/corpus.json"))
        parsed = parser.parse_args(args)
        self.assertEqual("/development-v1.json", str(parsed.development_v1))
        self.assertEqual("/private/corpus.json", str(parsed.output))
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(args[:-4])

    def test_metadata_has_no_authority_or_runtime_effect(self):
        raw, _ = build(references())
        value = json.loads(raw)
        self.assertEqual("not-granted", value["authority"])
        self.assertNotIn("automatic_routing", value)
        self.assertNotIn("model", value)
        self.assertNotIn("endpoint", value)


if __name__ == "__main__":
    unittest.main()
