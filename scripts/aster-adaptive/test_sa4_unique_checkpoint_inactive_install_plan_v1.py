import unittest

import sa4_unique_checkpoint_inactive_install_plan_v1 as source


class InstallPlanTests(unittest.TestCase):
    def test_exact_create_exclusive_set(self):
        value = source.plan()
        self.assertEqual(2, len(value["changes"]))
        self.assertTrue(all(row["operation"] == "create-exclusive"
                            for row in value["changes"]))
        self.assertFalse(value["effect_authorized"])
        self.assertIn("no-reconciler-invocation", value["exclusions"])


if __name__ == "__main__":
    unittest.main()
