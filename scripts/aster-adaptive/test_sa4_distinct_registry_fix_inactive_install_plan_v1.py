import unittest

import sa4_distinct_registry_fix_inactive_install_plan_v1 as install


class Tests(unittest.TestCase):
    def test_sources_dependencies_and_predecessor_are_frozen(self):
        install.validate()
        self.assertEqual(3, len(install.CHANGES))
        self.assertEqual(16, len(install.INSTALLED_DEPENDENCIES))

    def test_create_only_and_exact_reverse_rollback(self):
        value = install.plan()
        self.assertTrue(all(row["operation"] == "create-exclusive"
                            for row in value["changes"]))
        self.assertEqual(
            [item.destination for item in reversed(install.CHANGES)],
            value["rollback"]["remove-only-exact-after-hashes"])

    def test_inert_boundary(self):
        value = install.plan()
        self.assertFalse(value["effect_authorized"])
        self.assertEqual("off", value["automatic_routing"])
        self.assertIn("no-repair", value["exclusions"])
        self.assertIn("complete-v2-binding-accepts-and-restores-v1",
                      value["postcheck"])


if __name__ == "__main__":
    unittest.main()

