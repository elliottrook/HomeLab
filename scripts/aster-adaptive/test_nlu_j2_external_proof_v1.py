import copy
import hashlib
import unittest

import nlu_j2_external_proof_v1 as proof


PAYLOAD = b"aster-j2-proof-payload-v1"
KEY = {
    "kty": "RSA", "e": 65537,
    "n": "b28550dbcbe5fd5e86ef5d32fa2a8870978d98de05fd0cb2a916f17de68905698d1d102258f86655820c4adaafbe4175eae758d859ff9e42a1707fdaacf7682254fb96e93c0d01bf24b56cd957fd0c50d7fc1550b385e9375a7b983e4ce26caa5919145a4b257621e4977013a8f9256f479bb57e2a39c0bca1c612a9a32f02c3b809635a5edbcbb41fdb3356912331507b688ca0c80605970b4407f8ae0e99e2cf29ba70cfd022535e273aa0754d85e822eca0e10c5918b7817eb5533d445094cae641f2c7ba65a02bcd7a81fe08607605f83d0becf56be3bffd80376e9f93baa19dd49993daa092a926970b52eceeff36b3b210a6e1bb1dc20a3d1e7e8f1b51",
}
SIGNATURE = "6b449ef1e23b947445ce7e0142d16d94cd5064cb63be1040f9102416dcb8892d6d4111ee8e13200e2e2b9a87f3f0c89ac5f4a4ac39651fed438fd3a5bf0bde3ca974da9136ebf99e127ce156fb2ea2c407e6726a693e9be5a55c22e1e919ae2496a1a0433b58cbc616f7a1d11be0df843885f923cb0704aac8118c62218fbd342121b8860479f63793fff26c23a47eca5908bdc94d3a73b840961405e837f801c46b1dfa5c6709791e7d36acb148b179b3b6be97f8b37769df3cf1d2de9af2575c63607b65f1c95d8f97080527e12b26804306caf29c393fd452275dec6466a574aeb436d638098bae8cbf92d2c7ea309bef4227ad4fcdcfe98f4e021c954c5a"


def envelope():
    return {
        "schema": "aster-nlu-j2-external-proof.v1",
        "proof_scope": "corpus-custody",
        "signer_id": "external-corpus-custodian",
        "signer_key_sha256": proof.key_sha256(KEY),
        "payload_sha256": hashlib.sha256(PAYLOAD).hexdigest(),
        "signature_algorithm": "rsa-pkcs1v1_5-sha256",
        "signature_hex": SIGNATURE,
        "authority": "not-granted",
    }


class J2ExternalProofTests(unittest.TestCase):
    def test_pinned_rsa_proof_verifies_without_granting_authority(self):
        value = proof.verify(proof.canonical(envelope()), PAYLOAD, KEY,
                             proof.key_sha256(KEY), "corpus-custody")
        self.assertTrue(value["signature_verified"])
        self.assertEqual("not-granted", value["authority"])

    def test_payload_scope_key_and_signature_drift_fail_closed(self):
        variants = []
        value = envelope(); value["proof_scope"] = "evaluation-custody"; variants.append((value, PAYLOAD, KEY))
        variants.append((envelope(), PAYLOAD + b"x", KEY))
        value = envelope(); value["signature_hex"] = "0" * 512; variants.append((value, PAYLOAD, KEY))
        changed_key = copy.deepcopy(KEY); changed_key["n"] = "a" + changed_key["n"][1:]
        variants.append((envelope(), PAYLOAD, changed_key))
        for value, payload, key in variants:
            with self.subTest(), self.assertRaises(ValueError):
                proof.verify(proof.canonical(value), payload, key,
                             proof.key_sha256(KEY), "corpus-custody")

    def test_duplicate_keys_and_noncanonical_signer_fail_closed(self):
        raw = proof.canonical(envelope()).replace(
            b'"authority":"not-granted"',
            b'"authority":"not-granted","authority":"not-granted"')
        with self.assertRaises(ValueError):
            proof.verify(raw, PAYLOAD, KEY, proof.key_sha256(KEY), "corpus-custody")
        value = envelope(); value["signer_id"] = " External-Custodian "
        with self.assertRaises(ValueError):
            proof.verify(proof.canonical(value), PAYLOAD, KEY,
                         proof.key_sha256(KEY), "corpus-custody")
        for modulus in ("0" + KEY["n"][1:], KEY["n"][:-1] + "0"):
            changed = dict(KEY, n=modulus)
            with self.subTest(modulus=modulus[:4]), self.assertRaises(ValueError):
                proof.key_sha256(changed)


if __name__ == "__main__": unittest.main()
