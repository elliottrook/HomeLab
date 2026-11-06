import hashlib
from pathlib import Path
import unittest

import sa4_public_trust_install_plan_v1 as install_plan


class SA4PublicTrustInstallPlanTests(unittest.TestCase):
    def setUp(self):
        self.absent = {
            install_plan.BASE + "/sa4_public_trust_candidate_v1.py",
            install_plan.CHECKPOINT,
        }

    def test_new_source_hashes_are_exact(self):
        root = Path(__file__).parents[2]
        self.assertEqual(install_plan.NEW_SHA256, {
            path: hashlib.sha256((root / source).read_bytes()).hexdigest()
            for path, source in install_plan.SOURCE_BY_PATH.items()
        })

    def test_plan_is_reversible_inactive_and_exact(self):
        value = install_plan.plan(
            observed_sha256=dict(install_plan.OLD_SHA256),
            absent_paths=set(self.absent))
        self.assertEqual(3, len(value["replacements"]))
        self.assertEqual("exclusive-create-no-follow",
                         value["creation"]["method"])
        self.assertEqual("none", value["service_action"])
        self.assertFalse(value["signing_ceremony_authorized"])
        self.assertFalse(value["effect_authorized"])
        self.assertEqual("retain-and-stop", value["rollback"]["on_uncertainty"])

    def test_stale_hash_or_changed_absence_set_fails_closed(self):
        changed = dict(install_plan.OLD_SHA256)
        changed[next(iter(changed))] = "0" * 64
        for hashes, absent in (
            (changed, self.absent),
            (install_plan.OLD_SHA256, {install_plan.CHECKPOINT}),
            (install_plan.OLD_SHA256, self.absent | {"/tmp/extra"}),
        ):
            with self.assertRaises(ValueError):
                install_plan.plan(observed_sha256=hashes,
                                  absent_paths=set(absent))


if __name__ == "__main__":
    unittest.main()
