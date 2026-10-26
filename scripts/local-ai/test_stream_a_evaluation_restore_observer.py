import json
import subprocess
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stream_a_evaluation_restore_observer import (
    GpuHolder, collect_restore_observation, main, require_exact_gpu_holder, scan_gpu_holders,
)


class RestoreObserverTests(unittest.TestCase):
    def test_exact_read_only_probe_set_produces_accepted_observation(self):
        commands = []

        def runner(command, **kwargs):
            commands.append(command)
            command = tuple(command)
            if command[-2:] == ("is-active", "aster-llama.service"):
                return subprocess.CompletedProcess(command, 0, "active\n", "")
            if (any("aster-llama-production-auth-probe" in item for item in command)
                    or "ss" in command):
                return subprocess.CompletedProcess(command, 0, "", "")
            if command[0:2] == ("systemctl", "is-enabled"):
                value = "disabled\n" if "20261027" not in command[-1] else "not-found\n"
                return subprocess.CompletedProcess(command, 1, value, "")
            if command[0:2] == ("systemctl", "is-active"):
                return subprocess.CompletedProcess(command, 3, "inactive\n", "")
            if "aster-d4-candidate-h.service" in command:
                return subprocess.CompletedProcess(command, 3, "inactive\n", "")
            if "pgrep" in command:
                return subprocess.CompletedProcess(command, 1, "", "")
            raise AssertionError(command)

        with patch("stream_a_evaluation_restore_observer.scan_gpu_holders", return_value=(GpuHolder(
                42, 99, "/lxc/110/ns/system.slice/aster-llama.service",
                "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server"),)):
            result = collect_restore_observation(
                runner,
                lease_id="stream-a-evaluation-2026-10-27-0123456789abcdef",
                generation=1,
            )
        self.assertTrue(result["backend_active"])
        self.assertEqual(result["lease_id"],
                         "stream-a-evaluation-2026-10-27-0123456789abcdef")
        self.assertEqual(result["generation"], 1)
        self.assertEqual(result["gpu_holders"], ["lxc110:aster-llama.service"])
        self.assertEqual(result["evaluation_children"], [])
        self.assertEqual(len(result["f2_timers"]), 4)
        self.assertEqual(commands[0],
                         ("pct", "exec", "110", "--", "systemctl", "is-active", "aster-llama.service"))

    def test_probe_failure_or_wrong_holder_fails_closed(self):
        def failed(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, "", "failed")

        with self.assertRaises(RuntimeError):
            collect_restore_observation(failed, lease_id="eval-1", generation=1)

    def test_no_holder_extra_holder_and_foreign_holder_fail_closed(self):
        accepted = GpuHolder(42, 99, "/lxc/110/ns/system.slice/aster-llama.service",
                             "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server")
        foreign = GpuHolder(43, 100, "/lxc/999/ns/system.slice/other.service",
                            "/usr/bin/other-gpu-client")
        for holders in ((), (accepted, foreign), (foreign,)):
            with self.subTest(holders=holders), self.assertRaises(RuntimeError):
                require_exact_gpu_holder(holders)

    def test_pid_churn_during_gpu_scan_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            proc = Path(root) / "42"
            (proc / "fd").mkdir(parents=True)
            (proc / "fd" / "3").symlink_to("/dev/dri/renderD128")
            with self.assertRaises(RuntimeError):
                scan_gpu_holders(Path(root))

    def test_fully_exited_gpu_holder_is_ignored_and_scan_continues(self):
        with tempfile.TemporaryDirectory() as root:
            proc = Path(root) / "42"
            (proc / "fd").mkdir(parents=True)
            fd = proc / "fd" / "3"
            fd.symlink_to("/dev/dri/renderD128")
            real_readlink = __import__("os").readlink

            def exit_after_fd_observation(path):
                target = real_readlink(path)
                if Path(path) == fd:
                    shutil.rmtree(proc)
                return target

            with patch("stream_a_evaluation_restore_observer.os.readlink",
                       side_effect=exit_after_fd_observation):
                self.assertEqual(scan_gpu_holders(Path(root)), ())

    def test_observer_requires_explicit_gate(self):
        self.assertEqual(main([]), 0)

    def test_copied_wrapper_is_inert_then_forwards_authorized_arguments(self):
        wrapper_source = (Path(__file__).resolve().parent.parent.parent /
                          "services/local-ai-lease/stream-a-evaluation-restore-observe")
        module_source = Path(__file__).resolve().parent / "stream_a_evaluation_restore_observer.py"
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            module = root / "stream_a_evaluation_restore_observer.py"
            shutil.copy2(module_source, module)
            wrapper = root / "wrapper"
            wrapper.write_text(wrapper_source.read_text().replace(
                "/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_restore_observer.py",
                str(module)))
            wrapper.chmod(0o755)
            inert = subprocess.run(["/bin/sh", str(wrapper)], check=True,
                                   capture_output=True, text=True)
            self.assertEqual(json.loads(inert.stdout),
                             {"effects": "disabled", "state": "source-only"})
            fake = root / "fake_restore_observer.py"
            fake.write_text("import json, sys; print(json.dumps(sys.argv[1:]))\n")
            authorized_wrapper = root / "authorized-wrapper"
            authorized_wrapper.write_text(wrapper_source.read_text().replace(
                "/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_restore_observer.py",
                str(fake)))
            authorized_wrapper.chmod(0o755)
            authorized = subprocess.run(
                ["/bin/sh", str(authorized_wrapper), "--lease-id", "eval-1",
                 "--generation", "7", "--observe-authorized"],
                check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(authorized.stdout), [
                "--lease-id", "eval-1", "--generation", "7", "--observe-authorized"])


if __name__ == "__main__":
    unittest.main()
