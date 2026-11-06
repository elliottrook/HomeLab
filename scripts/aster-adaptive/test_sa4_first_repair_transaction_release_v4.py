import unittest
from unittest import mock

import sa4_first_repair_transaction_release_v4 as release


class SA4FirstRepairTransactionReleaseV4Tests(unittest.TestCase):
    def test_static_sources_and_inactive_install_are_exact(self):
        release.validate_static_evidence()
        release.validate_retained_packet()
        self.assertEqual(5, len(release.SOURCES))
        self.assertEqual(64, len(release.packet_sha256()))

    def test_fresh_authority_cannot_reuse_prior_approval(self):
        authority = release.packet()["required_fresh_authority"]
        self.assertEqual("new-exact-plan-detached-proof", authority["owner"])
        self.assertEqual("new-exact-plan-one-use-grant-and-proof",
                         authority["ai_pam"])
        self.assertFalse(authority["prior_approval_reusable"])

    def test_runtime_controls_are_created_by_owner_not_preasserted(self):
        runtime = release.packet()["required_fresh_runtime"]
        self.assertEqual("owner-created-exclusively-at-runtime",
                         runtime["operation_lock"])
        self.assertEqual("owner-created-plan-bound-at-runtime",
                         runtime["emergency_stop"])
        self.assertTrue(runtime["installed_hash_recheck"])

    def test_candidate_has_no_authority_effect_retry_or_restart(self):
        value = release.packet()
        self.assertEqual("release-candidate-awaiting-new-exact-repair-approval",
                         value["status"])
        self.assertFalse(value["effect_authorized"])
        self.assertFalse(value["transaction_limits"]["automatic_retry"])
        self.assertFalse(value["transaction_limits"]["service_restart"])
        self.assertEqual(1, value["transaction_limits"]["maximum_repairs"])
        self.assertEqual(1, value["transaction_limits"]["maximum_rollbacks"])

    def test_inert_install_mutation_fails_closed(self):
        mutated = release.upgrade_result.validate(
            release.UPGRADE_RESULT.read_bytes()).copy()
        mutated["inactive"] = False
        with mock.patch.object(release.upgrade_result, "validate",
                               return_value=mutated):
            with self.assertRaises(ValueError):
                release.validate_static_evidence()


if __name__ == "__main__":
    unittest.main()
