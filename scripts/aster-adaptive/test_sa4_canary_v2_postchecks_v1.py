import unittest
from pathlib import Path

import sa4_canary_v2_consumer_health_check_v1 as consumer
import sa4_canary_v2_target_bytes_check_v1 as bytes_check
import sa4_canary_v2_target_metadata_check_v1 as metadata


ROOT = Path(__file__).parents[2]
HEALTHY = (ROOT / "scripts/aster-adaptive/fixtures/"
           "sa4-canary-adapter-v2-healthy.json").read_bytes()


class Tests(unittest.TestCase):
    def test_healthy_v2_candidate_passes_byte_and_consumer_checks(self):
        self.assertEqual("pass", bytes_check.check(HEALTHY)["state"])
        self.assertEqual("pass", consumer.check(HEALTHY)["state"])

    def test_exact_v2_metadata_passes(self):
        value = {
            "device": 1, "inode": 2, "uid": 0, "gid": 0, "mode": "0644",
            "link_count": 1, "size": 85, "regular_file": True,
            "symlink": False, "bytes_sha256": bytes_check.EXPECTED_SHA256,
        }
        self.assertEqual("pass", metadata.check(value)["state"])

    def test_v1_candidate_is_rejected(self):
        old = (ROOT / "scripts/aster-adaptive/fixtures/"
               "sa4-canary-adapter-v1-healthy.json")
        if old.exists():
            with self.assertRaises(ValueError):
                bytes_check.check(old.read_bytes())


if __name__ == "__main__":
    unittest.main()
