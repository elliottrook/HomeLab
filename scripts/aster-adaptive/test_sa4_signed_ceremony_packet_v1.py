import unittest

import sa4_authenticated_authority_v1 as authority
import sa4_first_signed_ceremony_v1 as unsigned
import sa4_signed_ceremony_packet_v1 as ceremony
import sa4_single_file_repair_contract_v1 as contract


def verified(**changes):
    value = {
        "schema": "aster-sa4-authenticated-authority.v1",
        "authority_authenticated": True,
        "grant_consumed": False,
        "maximum_effects": 0,
        "preflight_eligible": False,
        "automatic_routing": "off",
    }
    value.update(changes)
    return value


class SA4SignedCeremonyPacketTests(unittest.TestCase):
    def test_assembles_exact_proofs_and_retains_zero_effect(self):
        packet = unsigned.build_unsigned(1_000)
        observed = {}

        def verifier(*arguments):
            observed["arguments"] = arguments
            return verified()

        value = ceremony.assemble_and_verify(
            packet, "a" * 512, "b" * 512, 1_000, verifier=verifier)
        self.assertFalse(value["effect_authorized"])
        self.assertEqual(0, value["maximum_effects"])
        approval = contract.decode_unique_json(value["approval_proof"])
        grant = contract.decode_unique_json(value["grant_proof"])
        self.assertEqual("a" * 512, approval["signature_hex"])
        self.assertEqual("b" * 512, grant["signature_hex"])
        self.assertEqual(value["approval_proof"], observed["arguments"][2])
        self.assertEqual(value["grant_proof"], observed["arguments"][4])
        self.assertEqual(1_000, observed["arguments"][5])

    def test_signature_shape_fails_closed_before_verifier(self):
        packet = unsigned.build_unsigned(1_000)
        for signature in ("a" * 510, "A" * 512, "g" * 512, 5):
            with self.subTest(signature=signature):
                with self.assertRaises(ValueError):
                    ceremony.assemble_and_verify(
                        packet, signature, "b" * 512, 1_000,
                        verifier=lambda *unused: verified())

    def test_effectful_or_consumed_verifier_result_fails_closed(self):
        packet = unsigned.build_unsigned(1_000)
        for result in (
            verified(maximum_effects=1),
            verified(grant_consumed=True),
            verified(preflight_eligible=True),
            verified(automatic_routing="on"),
        ):
            with self.subTest(result=result):
                with self.assertRaises(ValueError):
                    ceremony.assemble_and_verify(
                        packet, "a" * 512, "b" * 512, 1_000,
                        verifier=lambda *unused, result=result: result)

    def test_changed_statement_fails_closed(self):
        packet = unsigned.build_unsigned(1_000)
        statement = contract.decode_unique_json(packet["grant_statement"])
        statement["proof_scope"] = "owner-approval"
        packet["grant_statement"] = authority.canonical(statement)
        with self.assertRaises(ValueError):
            ceremony.assemble_and_verify(
                packet, "a" * 512, "b" * 512, 1_000,
                verifier=lambda *unused: verified())


if __name__ == "__main__":
    unittest.main()
