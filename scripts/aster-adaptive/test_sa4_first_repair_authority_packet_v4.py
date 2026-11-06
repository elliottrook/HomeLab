import unittest

import sa4_authenticated_authority_v1 as authority
import sa4_first_repair_authority_packet_v4 as packet_source
import sa4_first_repair_transaction_release_v4 as release
import sa4_single_file_repair_contract_v1 as contract


class SA4FirstRepairAuthorityPacketV4Tests(unittest.TestCase):
    def test_packet_binds_exact_v4_plan_and_unique_grant(self):
        packet = packet_source.build_unsigned(1_000)
        approval = contract.decode_unique_json(packet["approval"])
        grant = contract.decode_unique_json(packet["grant"])
        self.assertEqual(release.PLAN_SHA256,
                         authority.sha256(packet["plan"]))
        self.assertEqual(release.PLAN_SHA256, approval["plan_sha256"])
        self.assertEqual(release.PLAN_SHA256, grant["plan_sha256"])
        self.assertEqual(packet_source.GRANT_ID, grant["grant_id"])
        self.assertNotEqual("sa4-canary-first-grant-v1", grant["grant_id"])

    def test_authority_is_short_lived_and_one_use(self):
        packet = packet_source.build_unsigned(1_000)
        approval = contract.decode_unique_json(packet["approval"])
        grant = contract.decode_unique_json(packet["grant"])
        self.assertEqual(2_800, approval["expires_epoch"])
        self.assertEqual(1_900, grant["expires_epoch"])
        self.assertEqual(1, grant["max_uses"])
        self.assertEqual("approve-one-repair", approval["decision"])

    def test_unsigned_statements_bind_only_accepted_scopes(self):
        packet = packet_source.build_unsigned(1_000)
        for scope, payload, statement in (
                ("owner-approval", "approval", "approval_statement"),
                ("ai-pam-grant", "grant", "grant_statement")):
            value = contract.decode_unique_json(packet[statement])
            self.assertEqual(scope, value["proof_scope"])
            self.assertEqual(authority.sha256(packet[payload]),
                             value["payload_sha256"])
            self.assertNotIn("signature_hex", value)

    def test_invalid_time_fails_closed(self):
        for value in (0, -1, 1.5, "100"):
            with self.assertRaises(ValueError):
                packet_source.build_unsigned(value)


if __name__ == "__main__":
    unittest.main()
