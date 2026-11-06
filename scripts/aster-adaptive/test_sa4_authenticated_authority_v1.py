import copy
import unittest
from unittest.mock import patch

import sa4_authenticated_authority_v1 as authority
import sa4_single_file_repair_contract_v1 as repair
from test_sa4_single_file_repair_contract_v1 import plan


OWNER_KEY = {"kty": "RSA", "e": 65537, "n": "c500bb092fb6238804898283527bbfe72b2e29716097c0828fda68757c140f18c1fc647bd9eb5f19a10f27844c3b3ffabbd556144029789d59927fba388deee1288a112b9b90ad152582fbb8d34a1f28d57ca09ac5b851f6191a902ad034d68c71bd6dd764f72c4996b382c4dcd0560ac3bb52b5baff1294a60959da15f1e3da2ab950e9e95b0e39fefa6f2e9599899babcf2b9ef7300b378873fd8dd61174d9aa347a9cf26ca0c781026f4a893df928dde78061cad949388b1e5eaf4d9c49c065fa628f21701ad9d3614d85cd32623d44b401d4674f903713c8387201009fab19e36d70e59f03d0a16c28c557a2b98c7ccc82877524391a7cc220a66f08dd8b"}
PAM_KEY = {"kty": "RSA", "e": 65537, "n": "d25852ec06c2d37eeeb577b527b796efa2e73328f4d1056cc964452b5f0ec60e231b27ed26a02d07ce77af6dd5b0cd8faa3a99f47d561434f553f12d170242bb6b28435d08876ae0b3e1f8a8c026b3114c793d850e231834ddfa0aaae5a2a1f8dd1afd9e89964f59ccd078e84506487cb1d1b56a9aec0e36b94e4e721d99753f1df5254d5fdd97d067f2f44fadb8243b25ce0b6d619223a5bb7d32121c89b40e9d0275919363dc7d5215ce0f8d011acd64a46e7b566866bc7aa2ccb069e36d1352bd9e059b6d8af284a9586b2194fc8ad05d63334bd74a7d705cf8e892c06b747a2877bb99d0cf7dc1a1d9167a78549fb590a0bc0e08f77528ad0929b9afa143"}
OWNER_SIGNATURE = "a48601dbe6a6788af6ed937bfc4f058d29f43aaf44b6631029165e2a2a4f84d5809407fc5621fd75ab51e1c3dbd76103e157fffc836794e47471b7938b22bf071ed9585c00ecbf81a7cdf6348462917a2b907e2c1b1d39c0a9653acad7c47a245a4ea62adcf9eba6e0d8e45db84843530c21f5e051930a7d085297aeb3c8126baf09303c1288ac11d3895c181bdbe4415da19654bf89bf2d4b7d4dda9902803ecbe374eecda4a05d4573f970189917577a4b2fdec3723048a16713fa7f1b6eaef315b55ea25127a4600ffa3a406edbee0e8b16e987de4fe4fe2e77f7e3512304cb1e59a863535861eb4b94e19d516ca6865ba7a0b8e736cf6354b0bef5e8c624"
PAM_SIGNATURE = "7c59e888903e77a71f8792ed521fa02db7bc5d3cc7b8f7be63a79a091ca2edc0afae0ccc1fd67dae182dcb9a4512ec61808ab61cde76a5775af42d20810647c22d022b5bed4696eadbaee4ede39021bdd17567522f0045d97e87838ccd0a84624b9c7bb9fc4311c49c511ff56ecd6e64a675d4e0cc16d6c37dcf876c88c39205bf0e8d58f655166ab9bb7f05b87ad41bc022326be3aef1e2043816099a26a51f7deaa367cc94f63f5a39d2349cc457f7727e651a27198823241880cc0428a2f5c27ba36b3a03e4c4c5e17fe1d77126afe28189fb2d846b40946eb67674623d6e4b54736cad4c9f6c384d7c975d762c27723c9aafc630319321b44070cfb5e7c4"


def inputs():
    plan_raw = repair.canonical(plan()); digest = authority.sha256(plan_raw)
    approval = {"schema": "aster-sa4-owner-approval.v1",
                "plan_sha256": digest, "owner_id": "owner-reviewer",
                "decision": "approve-one-repair", "expires_epoch": 200,
                "scope": "exact-plan-only", "authority": "one-use-owner-approval"}
    grant = {"schema": "aster-sa4-ai-pam-grant.v1", "plan_sha256": digest,
             "grant_id": "synthetic-grant", "target_sha256": "2" * 64,
             "max_uses": 1, "expires_epoch": 150,
             "scope": "exact-target-atomic-replace", "authority": "one-use-ai-pam"}
    approval_raw, grant_raw = repair.canonical(approval), repair.canonical(grant)
    proofs = []
    for scope, signer, key, payload, signature in (
            ("owner-approval", "owner-reviewer", OWNER_KEY, approval_raw, OWNER_SIGNATURE),
            ("ai-pam-grant", "ai-pam-custodian", PAM_KEY, grant_raw, PAM_SIGNATURE)):
        proofs.append(authority.canonical({
            "schema": "aster-sa4-detached-proof.v1", "proof_scope": scope,
            "signer_id": signer, "signer_key_sha256": authority.key_sha256(key),
            "payload_sha256": authority.sha256(payload),
            "signature_algorithm": "rsa-pkcs1v1_5-sha256",
            "signature_hex": signature, "authority": "signature-only-no-effect"}))
    trusted = {
        "owner-approval": {authority.key_sha256(OWNER_KEY): {
            "signer_id": "owner-reviewer", "key": OWNER_KEY}},
        "ai-pam-grant": {authority.key_sha256(PAM_KEY): {
            "signer_id": "ai-pam-custodian", "key": PAM_KEY}},
    }
    return plan_raw, approval_raw, proofs[0], grant_raw, proofs[1], trusted


class SA4AuthenticatedAuthorityTests(unittest.TestCase):
    def test_two_distinct_compiled_signers_verify_but_cannot_authorize_effect(self):
        values = inputs();
        with patch.object(authority, "TRUSTED_KEYS", values[-1]):
            result = authority.verify(*values[:-1], now_epoch=100)
        self.assertTrue(result["authority_authenticated"])
        self.assertFalse(result["grant_consumed"])
        self.assertEqual(0, result["maximum_effects"])
        self.assertFalse(result["preflight_eligible"])

    def test_unrelated_signers_fail_against_exact_compiled_registry(self):
        values = inputs()
        with self.assertRaisesRegex(ValueError, "not compiled"):
            authority.verify(*values[:-1], now_epoch=100)
        self.assertEqual({"owner-approval": 1, "ai-pam-grant": 1},
                         {role: len(keys) for role, keys in
                          authority.TRUSTED_KEYS.items()})

    def test_payload_signature_scope_expiry_and_role_drift_fail_closed(self):
        plan_raw, approval_raw, approval_proof, grant_raw, grant_proof, trusted = inputs()
        variants = []
        changed = repair.decode_unique_json(approval_raw); changed["expires_epoch"] = 100
        variants.append((repair.canonical(changed), approval_proof, grant_raw, grant_proof, 100))
        changed = bytearray(approval_proof); changed[-3] ^= 1
        variants.append((approval_raw, bytes(changed), grant_raw, grant_proof, 100))
        changed = repair.decode_unique_json(grant_proof); changed["proof_scope"] = "owner-approval"
        variants.append((approval_raw, approval_proof, grant_raw, repair.canonical(changed), 100))
        same = copy.deepcopy(trusted)
        pam_fp = authority.key_sha256(PAM_KEY)
        same["ai-pam-grant"][pam_fp]["signer_id"] = "owner-reviewer"
        for approval, proof, grant, grant_proof_value, now in variants:
            with self.subTest(), patch.object(authority, "TRUSTED_KEYS", trusted), self.assertRaises(ValueError):
                authority.verify(plan_raw, approval, proof, grant, grant_proof_value, now)
        with patch.object(authority, "TRUSTED_KEYS", same), self.assertRaises(ValueError):
            authority.verify(plan_raw, approval_raw, approval_proof,
                             grant_raw, grant_proof, 100)

    def test_duplicate_keys_and_noncanonical_rsa_fail_closed(self):
        values = inputs()
        duplicate = values[2].replace(
            b'"authority":"signature-only-no-effect"',
            b'"authority":"signature-only-no-effect","authority":"signature-only-no-effect"')
        with patch.object(authority, "TRUSTED_KEYS", values[-1]), self.assertRaises(ValueError):
            authority.verify(values[0], values[1], duplicate,
                             values[3], values[4], 100)
        with self.assertRaises(ValueError):
            authority.key_sha256(dict(OWNER_KEY, n="0" + OWNER_KEY["n"][1:]))


if __name__ == "__main__":
    unittest.main()
