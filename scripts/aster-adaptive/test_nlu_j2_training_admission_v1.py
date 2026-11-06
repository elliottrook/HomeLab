import copy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

import nlu_j2_custody_receipt_v1 as custody
import nlu_j2_disjointness_proof_v1 as disjoint
import nlu_j2_owner_acceptance_v1 as owner
import nlu_j2_training_admission_v1 as admission


RECIPE = Path(__file__).parent / "fixtures" / "nlu-j2-training-recipe-manifest-v1.json"


def hashed(value):
    value = copy.deepcopy(value)
    value["receipt_sha256"] = custody._digest(value)
    return custody.canonical(value)


CORPUS = {
    "schema": "aster-nlu-j2-corpus-custody.v1",
    "manifest_sha256": custody.MANIFEST_SHA256,
    "custodian_id": "independent-j2-corpus-custodian",
    "reviewer_id": "independent-j2-label-reviewer",
    "corpus_sha256": disjoint.CORPUS_SHA256,
    "normalized_text_set_sha256": disjoint.CORPUS_SET_SHA256,
    "label_review_sha256": admission.LABEL_REVIEW_SHA256,
    "quality_review_sha256": admission.QUALITY_REVIEW_SHA256,
    "train_rows": 768, "validation_rows": 192, "labels": 16,
    "overlap_reference_count": 8, "normalized_overlap": 0,
    "content_in_receipt": False, "authority": "not-granted",
}
EVALUATION = {
    "schema": "aster-nlu-j2-evaluation-seal.v1",
    "manifest_sha256": custody.MANIFEST_SHA256,
    "custodian_id": "independent-j2-evaluation-custodian",
    "evaluation_sha256": "d" * 64,
    "normalized_text_set_sha256": "e" * 64,
    "cases": 32, "labels": 16, "cases_per_label": 2,
    "sealed_before_training": True, "trainer_access": "forbidden",
    "content_in_receipt": False, "authority": "not-granted",
}


def inputs():
    corpus_raw = hashed(CORPUS); evaluation_raw = hashed(EVALUATION)
    release = {
        "schema": "aster-nlu-j2-corpus-release-summary.v1",
        "manifest_sha256": custody.MANIFEST_SHA256,
        "corpus_sha256": disjoint.CORPUS_SHA256,
        "normalized_text_set_sha256": disjoint.CORPUS_SET_SHA256,
        "label_review_sha256": admission.LABEL_REVIEW_SHA256,
        "quality_review_sha256": admission.QUALITY_REVIEW_SHA256,
        "custody_receipt_sha256": hashlib.sha256(corpus_raw).hexdigest(),
        "rows": 960, "accepted": 960, "corrected": 0,
        "reference_count": 8, "normalized_overlap": 0,
        "corpus_release_eligible": True, "training_authorized": False,
        "authority": "not-granted", "automatic_routing": "off",
    }
    owner_raw = owner.canonical(owner.accepted_record("jason"))
    return [custody.canonical(release), owner_raw, RECIPE.read_bytes(),
            corpus_raw, b"corpus-proof", {"key": "corpus"},
            evaluation_raw, b"evaluation-proof", {"key": "evaluation"},
            b"disjointness", b"disjointness-proof"]


def external_result(scope):
    corpus = scope == "corpus-custody"
    return {"signer_id": ("independent-j2-corpus-custodian" if corpus else
                           "independent-j2-evaluation-custodian"),
            "signer_key_sha256": ("a" if corpus else "b") * 64}


def disjoint_result():
    return {"evaluation_sha256": "d" * 64,
            "evaluation_normalized_text_set_sha256": "e" * 64}


def invoke(values):
    trusted = {"independent-j2-corpus-custodian": "a" * 64,
               "independent-j2-evaluation-custodian": "b" * 64}
    with patch.dict(admission.TRUSTED_KEYS, trusted, clear=True), \
            patch.object(admission, "OWNER_ACCEPTANCE_FILE_SHA256",
                         hashlib.sha256(values[1]).hexdigest()):
        return admission.admit(*values)


class J2TrainingAdmissionTests(unittest.TestCase):
    def test_compiled_owner_trust_registry_is_exact(self):
        self.assertEqual(admission.TRUSTED_KEYS, {
            "independent-j2-corpus-custodian":
                "47feec850ae4dc67443249edcbc5c134c767e293c6dcc4bbede5a31c2749574c",
            "independent-j2-evaluation-custodian":
                "46685b0ebd4e1bcf65bfae35df4858373b2f928fe3f81ab267bfa58cedfa9498",
        })

    @patch("nlu_j2_training_admission_v1.disjointness.verify")
    @patch("nlu_j2_training_admission_v1.external.verify")
    def test_complete_chain_reaches_owner_review_without_authority(self, ext, dis):
        ext.side_effect = lambda _p, _r, _k, _h, scope: external_result(scope)
        dis.return_value = disjoint_result()
        value = invoke(inputs())
        self.assertEqual("eligible-for-owner-training-effect-review", value["status"])
        self.assertTrue(value["signatures_verified"])
        self.assertFalse(value["training_authorized"])
        self.assertFalse(value["deployment"])
        self.assertTrue(value["declared_roles_distinct"])
        self.assertEqual(hashlib.sha256(b"corpus-proof").hexdigest(),
                         value["corpus_proof_file_sha256"])

    @patch("nlu_j2_training_admission_v1.disjointness.verify")
    @patch("nlu_j2_training_admission_v1.external.verify")
    def test_release_owner_evaluation_and_key_drift_fail_closed(self, ext, dis):
        ext.side_effect = lambda _p, _r, _k, _h, scope: external_result(scope)
        dis.return_value = disjoint_result()
        changed = inputs(); release = custody.decode_unique_json(changed[0])
        release["normalized_overlap"] = 1; changed[0] = custody.canonical(release)
        with self.assertRaises(ValueError): invoke(changed)
        changed = inputs(); accepted = custody.decode_unique_json(changed[1])
        accepted["corpus_sha256"] = "0" * 64
        accepted["receipt_sha256"] = owner.receipt_sha256(accepted)
        changed[1] = owner.canonical(accepted)
        with self.assertRaises(ValueError): invoke(changed)
        dis.return_value = dict(disjoint_result(), evaluation_sha256="0" * 64)
        with self.assertRaises(ValueError): invoke(inputs())
        dis.return_value = disjoint_result()
        ext.side_effect = [external_result("corpus-custody"),
                           dict(external_result("evaluation-custody"),
                                signer_key_sha256="a" * 64)]
        with self.assertRaises(ValueError): invoke(inputs())
        changed = inputs(); evaluation = custody.decode_unique_json(changed[6])
        evaluation["custodian_id"] = CORPUS["reviewer_id"]
        copied = dict(evaluation); copied.pop("receipt_sha256")
        evaluation["receipt_sha256"] = custody._digest(copied)
        changed[6] = custody.canonical(evaluation)
        ext.side_effect = lambda _p, _r, _k, _h, scope: external_result(scope)
        with self.assertRaises(ValueError): invoke(changed)

    @patch("nlu_j2_training_admission_v1.disjointness.verify")
    @patch("nlu_j2_training_admission_v1.external.verify")
    def test_custody_digests_and_unpinned_keys_fail_closed(self, ext, dis):
        ext.side_effect = lambda _p, _r, _k, _h, scope: external_result(scope)
        dis.return_value = disjoint_result()
        changed = inputs(); corpus = custody.decode_unique_json(changed[3])
        corpus["corpus_sha256"] = "f" * 64
        copied = dict(corpus); copied.pop("receipt_sha256")
        corpus["receipt_sha256"] = custody._digest(copied)
        changed[3] = custody.canonical(corpus)
        release = custody.decode_unique_json(changed[0])
        release["custody_receipt_sha256"] = hashlib.sha256(changed[3]).hexdigest()
        changed[0] = custody.canonical(release)
        with self.assertRaisesRegex(ValueError, "cross-binding"):
            invoke(changed)
        values = inputs()
        with patch.dict(admission.TRUSTED_KEYS, {}, clear=True), \
                patch.object(admission, "OWNER_ACCEPTANCE_FILE_SHA256",
                             hashlib.sha256(values[1]).hexdigest()), \
                self.assertRaisesRegex(ValueError, "not owner-pinned"):
            admission.admit(*values)


if __name__ == "__main__": unittest.main()
