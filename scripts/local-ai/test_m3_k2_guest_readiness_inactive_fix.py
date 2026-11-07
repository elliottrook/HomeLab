import hashlib
import unittest

import m3_k2_guest_readiness_inactive_fix as fix


class K2GuestReadinessFixTests(unittest.TestCase):
    def test_exact_live_and_replacement_hashes_are_distinct(self):
        for old, new in fix.FILES.values():
            self.assertEqual(64, len(old))
            self.assertEqual(64, len(new))
            self.assertNotEqual(old, new)

    def test_correction_is_only_two_control_plane_files(self):
        self.assertEqual({"lab_hours_workloads.py",
                          "lab_hours_release_manifest.json"}, set(fix.FILES))

    def test_source_files_match_replacement_hashes(self):
        root = fix.Path(__file__).parent
        for name, (_, expected) in fix.FILES.items():
            self.assertEqual(expected,
                             hashlib.sha256((root / name).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
