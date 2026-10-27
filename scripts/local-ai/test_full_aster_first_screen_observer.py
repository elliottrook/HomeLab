import unittest

from full_aster_first_screen_candidate import UNIT
from full_aster_first_screen_observer import FixedObserver
from full_aster_first_screen_recovery import MOUNT_VALUE


class Runner:
    def __init__(self, config="", candidate="inactive", pids="", running=True):
        self.config=config; self.candidate=candidate; self.pids=pids; self.running=running
    def __call__(self, command, timeout):
        command=tuple(command)
        if command[:3] == ("pct", "config", "110"): return 0, self.config
        if command[:3] == ("pct", "status", "110"): return 0, "status: running" if self.running else "status: stopped"
        if command[-2:] == ("is-active", UNIT): return (3, self.candidate)
        if "pgrep" in command: return (1, self.pids) if not self.pids else (0, self.pids)
        if "sha256sum" in command:
            path=command[-1]
            values={"Qwen3.5-9B-Q4_K_M.gguf":"cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13",
                    "llama-server":"0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5",
                    "aster-llama.service":"a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3"}
            return 0, values[path.rsplit("/",1)[-1]]+"  "+path
        if command[-2:] == ("is-active", "aster-llama.service"): return 0, "active"
        if command[-1] == "/usr/local/sbin/aster-llama-production-auth-probe": return 0, ""
        raise AssertionError(command)


class ObserverTests(unittest.TestCase):
    def test_mount_classification_is_exact(self):
        self.assertEqual(FixedObserver(Runner()).mount_state(), "absent")
        self.assertEqual(FixedObserver(Runner("mp0: "+MOUNT_VALUE)).mount_state(), "exact")
        self.assertEqual(FixedObserver(Runner("mp0: /other,mp=/other")).mount_state(), "foreign")

    def test_exact_baseline_requires_absent_candidate_mount_and_all_hashes(self):
        self.assertTrue(FixedObserver(Runner()).exact_baseline_restored())
        self.assertFalse(FixedObserver(Runner("mp0: "+MOUNT_VALUE)).exact_baseline_restored())
        self.assertFalse(FixedObserver(Runner(pids="42")).exact_baseline_restored())


if __name__ == "__main__": unittest.main()
