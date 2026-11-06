import unittest

import sa4_target_registry_v2 as old
import sa4_target_registry_v3 as source


class Tests(unittest.TestCase):
    def test_v2_target_uses_distinct_postcheck_programs(self):
        new = source.resolve_production("sa4-lxc104-canary-adapter-v2")
        prior = old.resolve_production("sa4-lxc104-canary-adapter-v2")
        self.assertNotEqual(prior.postcheck_program_sha256,
                            new.postcheck_program_sha256)
        self.assertEqual(3, len(new.postcheck_program_sha256))
        self.assertNotEqual(old.registration_sha256(prior),
                            source.registration_sha256(new))


if __name__ == "__main__":
    unittest.main()
