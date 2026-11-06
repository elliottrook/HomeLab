import copy
import unittest

import sa4_authenticated_authority_v1 as authority
import sa4_independent_postcheck_receipt_v1 as observer
import sa4_public_trust_candidate_v1 as candidate


class SA4PublicTrustCandidateTests(unittest.TestCase):
    def test_candidate_compiles_exact_three_public_identities(self):
        candidate.validate()
        self.assertEqual(candidate.EXPECTED_DIGESTS, {
            role: authority.key_sha256(key)
            for role, key in candidate.PUBLIC_KEYS.items()
        })
        self.assertEqual(2, sum(len(v) for v in
                                candidate.AUTHORITY_TRUST_CANDIDATE.values()))
        self.assertEqual(1, len(candidate.OBSERVER_TRUST_CANDIDATE))

    def test_candidate_is_not_reachable_by_runtime_verifiers(self):
        self.assertEqual({"owner-approval": {}, "ai-pam-grant": {}},
                         authority.TRUSTED_KEYS)
        self.assertEqual({}, observer.TRUSTED_OBSERVERS)
        self.assertEqual("candidate-only-not-runtime-trusted",
                         candidate.SOURCE_REVIEW_STATUS)
        self.assertFalse(candidate.EFFECT_AUTHORIZED)
        self.assertEqual("off", candidate.AUTOMATIC_ROUTING)

    def test_any_key_or_digest_mutation_fails_closed(self):
        original_keys = candidate.PUBLIC_KEYS
        original_digests = candidate.EXPECTED_DIGESTS
        try:
            changed = copy.deepcopy(original_keys)
            changed["owner-approval"]["n"] = changed["owner-approval"]["n"][:-1] + "9"
            candidate.PUBLIC_KEYS = changed
            with self.assertRaises(ValueError): candidate.validate()
            candidate.PUBLIC_KEYS = original_keys
            candidate.EXPECTED_DIGESTS = dict(original_digests,
                                               **{"owner-approval": "0" * 64})
            with self.assertRaises(ValueError): candidate.validate()
        finally:
            candidate.PUBLIC_KEYS = original_keys
            candidate.EXPECTED_DIGESTS = original_digests


if __name__ == "__main__":
    unittest.main()
