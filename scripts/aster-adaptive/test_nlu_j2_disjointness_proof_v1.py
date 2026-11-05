import copy
import hashlib
import unittest

import nlu_j2_disjointness_proof_v1 as disjoint
import nlu_j2_external_proof_v1 as external
from test_nlu_j2_external_proof_v1 import KEY


SIGNATURE = "272d0c98b3484d978fcf6441cd475e72db3c7f891fb92d309ccc8298046168f09245c7be3af24fb54dbe882e722d10312aecf947709ea0026aca003ef0b82ae25b106f1154114e09bf37a397014200f5cbb0fb10968c1686a365d1564b569ff39069d16eee26681b8790994593a09505906b67404933bc030db3d60ceef71cf8846a2313e268661bdd407ff52a33cbd786474856afd830b0300b27c21a8ed195cb25da1b4521284e2d70f1a85695c174eb6f9fb41cdcae94038bd6ffd901bdfb31ae2c550bb22a0b7d91321b20b70de535d884d39eaefe60ee43c97310e623699926dc80fcbb5849c20f602ef20861a57476c13b419cdee7d6df637c1302f234"


def receipt():
    value = {
        "schema": "aster-nlu-j2-corpus-evaluation-disjointness.v1",
        "manifest_sha256": disjoint.MANIFEST_SHA256,
        "corpus_sha256": disjoint.CORPUS_SHA256,
        "corpus_normalized_text_set_sha256": disjoint.CORPUS_SET_SHA256,
        "evaluation_sha256": "d" * 64,
        "evaluation_normalized_text_set_sha256": "e" * 64,
        "corpus_rows": 960, "evaluation_cases": 32,
        "intersection_count": 0,
        "comparison_algorithm": "normalized-utf8-exact-set-v1",
        "custodian_id": "external-corpus-custodian",
        "content_in_receipt": False, "authority": "not-granted",
    }
    value["receipt_sha256"] = disjoint.receipt_sha256(value)
    return value


def proof(raw):
    return {
        "schema": "aster-nlu-j2-external-proof.v1",
        "proof_scope": "corpus-evaluation-disjointness",
        "signer_id": "external-corpus-custodian",
        "signer_key_sha256": external.key_sha256(KEY),
        "payload_sha256": hashlib.sha256(raw).hexdigest(),
        "signature_algorithm": "rsa-pkcs1v1_5-sha256",
        "signature_hex": SIGNATURE, "authority": "not-granted",
    }


class J2DisjointnessProofTests(unittest.TestCase):
    def test_signed_zero_intersection_receipt_verifies(self):
        raw = disjoint.canonical(receipt())
        value = disjoint.verify(raw, external.canonical(proof(raw)), KEY,
                                external.key_sha256(KEY))
        self.assertEqual(0, value["intersection_count"])
        self.assertTrue(value["signature_verified"])
        self.assertFalse(value["training_authorized"])

    def test_overlap_digest_and_signer_drift_fail_closed(self):
        for field, changed in (("intersection_count", 1),
                               ("corpus_rows", 959),
                               ("comparison_algorithm", "digest-inequality"),
                               ("evaluation_normalized_text_set_sha256",
                                disjoint.CORPUS_SET_SHA256)):
            value = receipt(); value[field] = changed
            value["receipt_sha256"] = disjoint.receipt_sha256(value)
            with self.subTest(field=field), self.assertRaises(ValueError):
                disjoint.validate_receipt(disjoint.canonical(value))
        raw = disjoint.canonical(receipt())
        signed = proof(raw); signed["signer_id"] = "other-custodian"
        with self.assertRaises(ValueError):
            disjoint.verify(raw, external.canonical(signed), KEY,
                            external.key_sha256(KEY))

    def test_self_hash_signature_and_duplicate_keys_fail_closed(self):
        value = receipt(); value["receipt_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            disjoint.validate_receipt(disjoint.canonical(value))
        raw = disjoint.canonical(receipt())
        signed = proof(raw); signed["signature_hex"] = "0" * 512
        with self.assertRaises(ValueError):
            disjoint.verify(raw, external.canonical(signed), KEY,
                            external.key_sha256(KEY))
        duplicate = raw.replace(b'"intersection_count":0',
                                b'"intersection_count":0,"intersection_count":0')
        with self.assertRaises(ValueError):
            disjoint.validate_receipt(duplicate)


if __name__ == "__main__": unittest.main()
