import hashlib
from pathlib import Path
import unittest

import sa4_distinct_canary_proposed_registry_v1 as proposed
import sa4_target_registry_v1 as production


class Tests(unittest.TestCase):
    def test_exact_proposed_target_and_artifacts(self):
        target = proposed.resolve_proposed("sa4-lxc104-canary-adapter-v2")
        self.assertEqual("/var/lib/aster/sa4/canary-adapter-v2.json", target.path)
        root = Path(__file__).parents[2]
        drifted = (root / "scripts/aster-adaptive/fixtures/sa4-canary-adapter-v2-drifted.json").read_bytes()
        healthy = (root / "scripts/aster-adaptive/fixtures/sa4-canary-adapter-v2-healthy.json").read_bytes()
        self.assertEqual(
            "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0",
            hashlib.sha256(drifted).hexdigest())
        self.assertEqual(
            "fae178a1558199b66f4dc9abec18690ed22a7cbee398f411b47f93daf1d3a0c2",
            hashlib.sha256(healthy).hexdigest())

    def test_proposal_is_not_production_resolvable(self):
        with self.assertRaises(ValueError):
            production.resolve_production("sa4-lxc104-canary-adapter-v2")

    def test_review_card_is_exact_and_pending(self):
        root = Path(__file__).parents[2]
        card = root / "docs/projects/AI Projects/evidence/SA4-distinct-canary-v2-owner-review-card-2026-11-06.json"
        raw = card.read_bytes()
        self.assertEqual(
            proposed.PROPOSED_TARGETS[0].owner_review_sha256,
            hashlib.sha256(raw).hexdigest())
        self.assertIn(b'"owner_decision":"pending"', raw)
        self.assertIn(b'"effect_authorized":false', raw)


if __name__ == "__main__":
    unittest.main()
