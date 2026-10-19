import unittest
from unittest.mock import patch

import f2_preflight_fixed_wrapper as wrapper
from f2_preflight_snapshot import CLOCK, EXCLUSION_TOKEN, LEASE_STATUS


class F2FixedWrapperTests(unittest.TestCase):
    def test_wrapper_owns_cycle_token_and_snapshot_path(self):
        calls = []
        def runner(command, timeout):
            calls.append(command)
            if command == CLOCK: return 0, "1792371600\n"
            if command == EXCLUSION_TOKEN: return 0, "lease-1\n"
            if command == LEASE_STATUS: return 0, '{"state":"ready"}'
            if command == wrapper.PVE_ARTIFACTS: return 0, "[]"
            return 1, ""
        with patch.object(wrapper, "write_snapshot") as write:
            with self.assertRaises(Exception):
                wrapper.capture_fixed_preflight(runner)
        self.assertEqual(calls[:2], [CLOCK, EXCLUSION_TOKEN])
        write.assert_not_called()

    def test_pin_map_is_fixed_and_complete(self):
        self.assertEqual(len(wrapper.EXPECTED_PINS), 5)
        self.assertIn("/usr/local/sbin/local-ai-lease", wrapper.EXPECTED_PINS)
        self.assertEqual(wrapper.SNAPSHOT_PATH, wrapper.SNAPSHOT_DIR / "current.json")


if __name__ == "__main__":
    unittest.main()
