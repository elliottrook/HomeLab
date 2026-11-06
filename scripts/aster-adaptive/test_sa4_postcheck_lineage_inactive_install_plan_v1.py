import unittest

import sa4_postcheck_lineage_inactive_install_plan_v1 as source


class Tests(unittest.TestCase):
    def test_exact_create_only_install(self):
        value = source.plan()
        self.assertEqual(8, len(value["changes"]))
        self.assertTrue(all(row["operation"] == "create-exclusive"
                            for row in value["changes"]))
        self.assertFalse(value["effect_authorized"])

    def test_fresh_paths_are_v4(self):
        self.assertTrue(all(path.endswith("-v4")
                            for path in source.plan()["fresh_paths"]))


if __name__ == "__main__":
    unittest.main()
