import copy
import hashlib
from pathlib import Path
import unittest

import sa4_authenticated_authority_v1 as authority
import sa4_independent_postcheck_receipt_v1 as observer
import sa4_key_custody_slots_v1 as custody
import sa4_public_trust_candidate_v1 as candidate


class SA4PublicTrustCandidateTests(unittest.TestCase):
    def test_owner_acceptance_is_hash_bound_to_promoted_slots(self):
        path = (Path(__file__).parents[2]
                / "docs/projects/AI Projects/evidence/SA4-public-trust-owner-acceptance-2026-11-05.json")
        self.assertEqual(custody.OWNER_ACCEPTANCE_SHA256,
                         hashlib.sha256(path.read_bytes()).hexdigest())

    def test_candidate_compiles_exact_three_public_identities(self):
        candidate.validate()
        self.assertEqual(candidate.EXPECTED_DIGESTS, {
            role: authority.key_sha256(key)
            for role, key in candidate.PUBLIC_KEYS.items()
        })
        self.assertEqual(2, sum(len(v) for v in
                                candidate.AUTHORITY_TRUST_CANDIDATE.values()))
        self.assertEqual(1, len(candidate.OBSERVER_TRUST_CANDIDATE))

    def test_owner_accepted_public_source_matches_runtime_verifiers(self):
        self.assertEqual(candidate.AUTHORITY_TRUST_CANDIDATE,
                         authority.TRUSTED_KEYS)
        self.assertEqual(candidate.OBSERVER_TRUST_CANDIDATE,
                         observer.TRUSTED_OBSERVERS)
        self.assertEqual("owner-accepted-source-trust",
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
