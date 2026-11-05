import hashlib
from pathlib import Path
import unittest

import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry


ROOT = Path(__file__).with_name("fixtures")
FIXTURES = {
    "drifted": (
        "sa4-canary-adapter-drifted-v1.json",
        "19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a"),
    "healthy": (
        "sa4-canary-adapter-healthy-v1.json",
        "4529dee5c9b58b607a9025b62aa3a4871660de98c4bafbb7fd69d7bc2a1e1065"),
}


class SA4FirstTargetReviewPacketTests(unittest.TestCase):
    def test_exact_canary_fixtures_are_canonical_small_and_distinct(self):
        observed = {}
        for state, (name, digest) in FIXTURES.items():
            raw = (ROOT / name).read_bytes()
            value = contract.decode_unique_json(raw)
            self.assertEqual(contract.canonical(value), raw)
            self.assertEqual(digest, hashlib.sha256(raw).hexdigest())
            self.assertLessEqual(len(raw), 4096)
            self.assertEqual({"adapter", "schema", "state"}, set(value))
            self.assertEqual("sa4-canary", value["adapter"])
            self.assertEqual("aster-sa4-canary-adapter.v1", value["schema"])
            self.assertEqual(state, value["state"])
            observed[state] = raw
        self.assertNotEqual(observed["drifted"], observed["healthy"])

    def test_review_packet_does_not_register_a_live_target(self):
        self.assertEqual((), registry.PRODUCTION_TARGETS)
        with self.assertRaises(ValueError):
            registry.resolve_production("sa4-lxc104-canary-adapter-v1")


if __name__ == "__main__":
    unittest.main()
