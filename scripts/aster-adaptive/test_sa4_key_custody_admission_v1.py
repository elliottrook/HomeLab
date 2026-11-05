import copy
import unittest

import sa4_key_custody_admission_v1 as admission
import sa4_single_file_repair_contract_v1 as contract


KEYS = (
    {"kty": "RSA", "e": 65537, "n": "c" + "1" * 511},
    {"kty": "RSA", "e": 65537, "n": "d" + "2" * 510 + "3"},
    {"kty": "RSA", "e": 65537, "n": "e" + "3" * 510 + "5"},
)


def candidate():
    roles = []
    values = (
        ("owner-approval", "human-owner-device", "owner-mac-signing-surface", "jason-owner"),
        ("ai-pam-grant", "ai-pam-broker", "broker-controlled-signer", "aster-ai-pam"),
        ("independent-observer", "proxmox-observer", "dedicated-observer-identity", "aster-observer"),
    )
    for key, (role, domain, location, signer) in zip(KEYS, values):
        roles.append({
            "role": role, "custody_domain": domain,
            "signer_location": location, "signer_id": signer,
            "public_key": key,
            "creation_method": "external-custodian-generated",
            "private_key_exported": False,
            "private_key_read_by_codex": False,
            "runtime_key_nomination": False,
        })
    return {
        "schema": "aster-sa4-key-custody-candidate.v1",
        "status": "candidate-for-owner-review",
        "target_id": "sa4-lxc104-canary-adapter-v1",
        "roles": roles,
        "authority": "public-trust-proposal-no-effect",
        "effect_authorized": False,
        "automatic_routing": "off",
    }


class SA4KeyCustodyAdmissionTests(unittest.TestCase):
    def test_exact_three_way_candidate_is_review_only(self):
        result = admission.validate_candidate(contract.canonical(candidate()))
        self.assertEqual(3, len(result["public_key_sha256_by_role"]))
        self.assertTrue(result["custody_domains_distinct"])
        self.assertTrue(result["ready_for_owner_review"])
        self.assertFalse(result["ready_for_installation"])
        self.assertFalse(result["private_material_accepted"])
        self.assertFalse(result["effect_authorized"])

    def test_reused_key_or_signer_fails_closed(self):
        for field in ("public_key", "signer_id"):
            value = candidate()
            value["roles"][1][field] = value["roles"][0][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                admission.validate_candidate(contract.canonical(value))

    def test_private_export_read_or_runtime_nomination_fails_closed(self):
        for field in ("private_key_exported", "private_key_read_by_codex",
                      "runtime_key_nomination"):
            value = candidate(); value["roles"][0][field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                admission.validate_candidate(contract.canonical(value))

    def test_role_order_domain_location_and_envelope_are_frozen(self):
        variants = []
        value = candidate(); value["roles"] = list(reversed(value["roles"])); variants.append(value)
        value = candidate(); value["roles"][1]["custody_domain"] = "human-owner-device"; variants.append(value)
        value = candidate(); value["roles"][2]["signer_location"] = "lxc104"; variants.append(value)
        value = candidate(); value["effect_authorized"] = True; variants.append(value)
        for value in variants:
            with self.assertRaises(ValueError):
                admission.validate_candidate(contract.canonical(value))


if __name__ == "__main__":
    unittest.main()
