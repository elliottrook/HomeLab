import unittest

import sa4_authenticated_authority_v1 as authority
import sa4_first_signed_ceremony_v1 as ceremony
import sa4_single_file_repair_contract_v1 as contract


class SA4FirstSignedCeremonyTests(unittest.TestCase):
    def test_unsigned_packet_is_exact_short_lived_and_zero_effect(self):
        packet = ceremony.build_unsigned(1_000)
        self.assertEqual({"plan", "approval", "approval_statement",
                          "grant", "grant_statement"}, set(packet))
        plan = contract.validate_plan(packet["plan"])
        approval = contract.decode_unique_json(packet["approval"])
        grant = contract.decode_unique_json(packet["grant"])
        self.assertFalse(plan["effect_authorized"])
        self.assertEqual(2_800, approval["expires_epoch"])
        self.assertEqual(1_900, grant["expires_epoch"])
        self.assertEqual(authority.sha256(packet["plan"]),
                         approval["plan_sha256"])
        self.assertEqual(approval["plan_sha256"], grant["plan_sha256"])

    def test_statements_bind_exact_payloads_and_accepted_public_keys(self):
        packet = ceremony.build_unsigned(1_000)
        for scope, payload_name, statement_name in (
            ("owner-approval", "approval", "approval_statement"),
            ("ai-pam-grant", "grant", "grant_statement"),
        ):
            value = contract.decode_unique_json(packet[statement_name])
            self.assertEqual(scope, value["proof_scope"])
            self.assertEqual(authority.sha256(packet[payload_name]),
                             value["payload_sha256"])
            self.assertEqual("signature-only-no-effect", value["authority"])
            self.assertNotIn("signature_hex", value)

    def test_bad_time_fails_closed(self):
        for value in (0, -1, 1.5, "100"):
            with self.assertRaises(ValueError): ceremony.build_unsigned(value)


if __name__ == "__main__":
    unittest.main()
