from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import nlu_j2_mac_host_owner_v1 as owner


class J2MacHostOwnerTests(unittest.TestCase):
    def test_swap_units_and_resource_shapes_are_strict(self):
        self.assertEqual(1024, owner._bytes("1K"))
        self.assertEqual(2 * 1024 ** 2, owner._bytes("2M"))
        self.assertEqual(round(1.5 * 1024 ** 3), owner._bytes("1.5G"))
        with self.assertRaises(ValueError): owner._bytes("unlimited")

        vm = subprocess.CompletedProcess([], 0, "Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free: 100.\nPages inactive: 200.\nPages speculative: 50.\n", "")
        swap = subprocess.CompletedProcess([], 0, "total = 2.00G  used = 12.50M  free = 1.99G\n", "")
        with patch.object(owner.subprocess, "run", side_effect=[vm, swap]):
            result = owner.resources()
        self.assertEqual(350 * 16384, result["available_bytes"])
        self.assertEqual(round(12.5 * 1024 ** 2), result["swap_used_bytes"])

    def test_exact_workload_and_input_pins_are_mandatory(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = [Path(temporary) / name for name in ("c", "r", "a", "m")]
            for path in paths: path.write_bytes(b"x")
            with self.assertRaisesRegex(ValueError, "pin changed"):
                owner.validate_inputs(*paths)

    def test_resource_or_process_admission_prevents_start(self):
        paths = [Path("c"), Path("r"), Path("a"), Path("m")]
        with patch.object(owner, "validate_inputs"), \
                patch.object(owner, "resources", return_value={
                    "available_bytes": owner.MIN_AVAILABLE_BYTES - 1,
                    "swap_used_bytes": 0}), \
                patch.object(owner.subprocess, "Popen") as popen, \
                self.assertRaisesRegex(RuntimeError, "memory admission"):
            owner.run(*paths, Path("output"))
        popen.assert_not_called()

        with patch.object(owner, "validate_inputs"), \
                patch.object(owner, "resources", return_value={
                    "available_bytes": owner.MIN_AVAILABLE_BYTES,
                    "swap_used_bytes": 0}), \
                patch.object(owner, "competing_processes", return_value=[42]), \
                patch.object(owner.subprocess, "Popen") as popen, \
                self.assertRaisesRegex(RuntimeError, "process admission"):
            owner.run(*paths, Path("output"))
        popen.assert_not_called()

    def test_termination_escalates_only_after_grace(self):
        process = MagicMock()
        process.pid = 123; process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired("x", 10), 0]
        with patch.object(owner.os, "killpg") as killpg:
            owner._terminate(process)
        self.assertEqual([owner.signal.SIGTERM, owner.signal.SIGKILL],
                         [call.args[1] for call in killpg.call_args_list])


if __name__ == "__main__": unittest.main()
