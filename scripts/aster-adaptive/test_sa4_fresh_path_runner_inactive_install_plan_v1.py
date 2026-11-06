import unittest

import sa4_fresh_path_runner_inactive_install_plan_v1 as source


class Tests(unittest.TestCase):
    def test_single_create_only_runner(self):
        value = source.plan()
        self.assertEqual("create-exclusive", value["change"]["operation"])
        self.assertFalse(value["effect_authorized"])
        self.assertEqual("off", value["automatic_routing"])

    def test_failed_and_fresh_paths_are_disjoint(self):
        value = source.plan()
        self.assertFalse(set(value["retained_failed_paths"])
                         & set(value["fresh_paths"]))


if __name__ == "__main__":
    unittest.main()
