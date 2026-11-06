import hashlib
from pathlib import Path
import unittest

import sa4_target_registry_v1 as previous
import sa4_target_registry_v2 as registry


class Tests(unittest.TestCase):
    def test_v1_registration_is_unchanged(self):
        old = previous.resolve_production("sa4-lxc104-canary-adapter-v1")
        new = registry.resolve_production("sa4-lxc104-canary-adapter-v1")
        self.assertEqual(
            previous.registration_sha256(old), registry.registration_sha256(new))

    def test_distinct_target_binds_owner_acceptance(self):
        target = registry.resolve_production("sa4-lxc104-canary-adapter-v2")
        self.assertEqual("/var/lib/aster/sa4/canary-adapter-v2.json", target.path)
        root = Path(__file__).parents[2]
        acceptance = root / "docs/projects/AI Projects/evidence/SA4-distinct-canary-v2-owner-acceptance-2026-11-06.json"
        self.assertEqual(
            target.owner_review_sha256,
            hashlib.sha256(acceptance.read_bytes()).hexdigest())

    def test_unknown_target_fails(self):
        with self.assertRaises(ValueError):
            registry.resolve_production("sa4-unregistered")


if __name__ == "__main__":
    unittest.main()
