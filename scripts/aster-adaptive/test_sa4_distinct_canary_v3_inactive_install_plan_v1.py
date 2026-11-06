import unittest

import sa4_distinct_canary_v3_inactive_install_plan_v1 as install


class Tests(unittest.TestCase):
    def test_sources_and_dependencies_are_frozen(self):
        install.validate()
        self.assertEqual(2, len(install.CHANGES))
        self.assertEqual(7, len(install.INSTALLED_DEPENDENCIES))

    def test_create_only_with_exact_reverse_rollback(self):
        value = install.plan()
        self.assertTrue(all(
            item["operation"] == "create-exclusive"
            for item in value["changes"]))
        self.assertEqual(
            [item.destination for item in reversed(install.CHANGES)],
            value["rollback"]["remove-only-exact-after-hashes"])

    def test_postcheck_is_inert_and_target_bound(self):
        value = install.plan()
        self.assertFalse(value["effect_authorized"])
        self.assertEqual("off", value["automatic_routing"])
        self.assertEqual(install.TARGET_SHA256, value["target"]["sha256"])
        self.assertIn("no-v3-runner-invocation", value["postcheck"])
        self.assertIn("no-repair", value["exclusions"])


if __name__ == "__main__":
    unittest.main()
