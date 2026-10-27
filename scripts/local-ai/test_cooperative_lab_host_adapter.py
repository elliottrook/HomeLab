import unittest

from cooperative_lab_host_adapter import CooperativeHostObserver
from cooperative_lab_session import _canonical_commands
from full_inference_lab_session import canonical_commands


class CooperativeLabHostAdapterTests(unittest.TestCase):
    def setUp(self):
        self.probes = 0

    def runner(self, argv, timeout):
        if "readlink" in argv:
            self.probes += 1
            return 0, "/dev/null\n"
        if "--property=UnitFileState" in argv:
            self.probes += 1
            return 0, "enabled\n"
        if "--property=ActiveState" in argv:
            self.probes += 1
            return 0, ("inactive\n" if self.probes == 2 else "active\n")
        if "ss" in argv:
            return 0, "ESTAB 0 0 192.168.70.12:11435 192.168.70.50:55000\n"
        return 1, ""

    def test_observes_only_canonical_effects(self):
        observer = CooperativeHostObserver(self.runner, allowed_backend_client="192.168.70.50")
        stop, restore = _canonical_commands()
        self.assertTrue(observer("mask", stop[0]))
        self.assertTrue(observer("unmask", restore[0]))
        self.assertTrue(observer("start", restore[1]))
        with self.assertRaisesRegex(Exception, "canonical"):
            observer("start", ("pct", "exec", "110", "--", "systemctl", "start", "bad.service"))

    def test_unknown_or_empty_backend_client_set_is_no_go(self):
        observer = CooperativeHostObserver(self.runner)
        self.assertFalse(observer.backend_client_exclusive())
        observer = CooperativeHostObserver(self.runner, allowed_backend_client="192.168.70.51")
        self.assertFalse(observer.backend_client_exclusive())

    def test_observer_accepts_full_drain_stop_and_timer_mask_phases(self):
        def full_runner(argv, timeout):
            if "readlink" in argv:
                return 0, "/dev/null\n"
            if "--property=UnitFileState" in argv:
                return 0, "masked-runtime\n"
            if "--property=ActiveState" in argv:
                return 0, "inactive\n"
            return 1, ""
        observer = CooperativeHostObserver(full_runner)
        drain, _ = canonical_commands()
        self.assertTrue(observer("stop", drain[0]))
        self.assertTrue(observer("mask", drain[3]))


if __name__ == "__main__":
    unittest.main()
