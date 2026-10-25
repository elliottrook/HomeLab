import subprocess
import unittest

from stream_a_evaluation_restore_observer import collect_restore_observation


class RestoreObserverTests(unittest.TestCase):
    def test_exact_read_only_probe_set_produces_accepted_observation(self):
        commands = []
        outputs = iter(("active\n", "", "", ""))

        def runner(command, **kwargs):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, next(outputs), "")

        result = collect_restore_observation(runner, lease_id="eval-1", generation=1)
        self.assertTrue(result["backend_active"])
        self.assertEqual(result["lease_id"], "eval-1")
        self.assertEqual(result["generation"], 1)
        self.assertEqual(result["gpu_holders"], ["lxc110:aster-llama.service"])
        self.assertEqual(commands[0],
                         ("pct", "exec", "110", "--", "systemctl", "is-active", "aster-llama.service"))

    def test_probe_failure_or_wrong_holder_fails_closed(self):
        def failed(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, "", "failed")

        with self.assertRaises(RuntimeError):
            collect_restore_observation(failed, lease_id="eval-1", generation=1)


if __name__ == "__main__":
    unittest.main()
