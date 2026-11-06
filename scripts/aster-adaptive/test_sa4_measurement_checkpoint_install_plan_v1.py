import hashlib
from pathlib import Path
import unittest

import sa4_measurement_checkpoint_install_plan_v1 as install


ROOT = Path(__file__).parents[2]


class SA4MeasurementCheckpointInstallPlanTests(unittest.TestCase):
    def test_source_hashes_match(self):
        for item in install.CHANGES:
            self.assertEqual(item.new_sha256, hashlib.sha256(
                (ROOT / item.source).read_bytes()).hexdigest())

    def test_packet_is_two_file_zero_effect_and_measurement_only(self):
        value = install.plan()
        self.assertEqual(2, len(value["changes"]))
        self.assertEqual("lxc104", value["host_id"])
        self.assertFalse(value["effect_authorized"])
        self.assertIn("one-read-only-live-measurement", value["postchecks"])
        self.assertIn("no-checkpoint-owner-invocation", value["exclusions"])
        self.assertIn("no-target-write-or-repair", value["exclusions"])


if __name__ == "__main__":
    unittest.main()
