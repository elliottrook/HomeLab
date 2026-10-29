import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import aster_llama_sa3_guest_wrapper as wrapper


class GuestWrapperTests(unittest.TestCase):
    def test_scope_is_deterministic_and_rejects_untrusted_identity(self):
        self.assertEqual(
            wrapper._scope_unit("lease-1", 2),
            "aster-llama-sa3-" + hashlib.sha256(b"lease-1:2").hexdigest()[:16] + ".scope")
        with self.assertRaises(wrapper.GuestError):
            wrapper._scope_unit("; reboot", 1)
        with self.assertRaises(wrapper.GuestError):
            wrapper._scope_unit("lease-1", 0)

    def test_server_command_is_fixed_and_credential_is_file_only(self):
        command = wrapper._server_command(Path("/run/sa3/api-key"), "sa3.scope")
        self.assertEqual(command[:8], (
            "/usr/bin/systemd-run", "--quiet", "--collect", "--scope",
            "--unit=sa3.scope", "/usr/sbin/runuser", "--user", "ollama"))
        self.assertIn("--api-key-file", command)
        self.assertIn("/run/sa3/api-key", command)
        self.assertNotIn("token", " ".join(command).lower())
        self.assertIn("--reasoning", command)

    def test_main_requires_and_forwards_all_fixed_bounds(self):
        captured = {}

        def fake_run(**kwargs):
            captured.update(kwargs)
            return {"ok": True}

        with mock.patch.object(wrapper, "run", side_effect=fake_run), \
             mock.patch("builtins.print") as printed:
            self.assertEqual(wrapper.main([
                "--profile", wrapper.PROFILE,
                "--port", str(wrapper.PORT),
                "--requests", str(wrapper.REQUESTS),
                "--per-request-timeout", str(wrapper.PER_REQUEST_TIMEOUT),
                "--deadline", str(wrapper.DEADLINE),
                "--lease-id", "lease-1", "--generation", "2",
                "--scope-unit", wrapper._scope_unit("lease-1", 2)]), 0)
        self.assertEqual(captured["deadline"], wrapper.DEADLINE)
        self.assertEqual(captured["per_request_timeout"], wrapper.PER_REQUEST_TIMEOUT)
        printed.assert_called_once_with(json.dumps({"ok": True}, sort_keys=True, separators=(",", ":")))

    def test_runtime_pin_check_excludes_keys_and_review_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, value in wrapper.PINS.items():
                path = root / name
                path.write_bytes((name + "\n").encode())
            old_pins = wrapper.PINS
            old_root = wrapper.RUNTIME_ROOT
            old_model, old_server = wrapper.MODEL_PATH, wrapper.SERVER
            old_model_sha, old_binary_sha = wrapper.MODEL_SHA, wrapper.BINARY_SHA
            try:
                wrapper.RUNTIME_ROOT = root
                wrapper.PINS = {
                    name: hashlib.sha256((name + "\n").encode()).hexdigest()
                    for name in old_pins
                }
                model = root / "model.gguf"
                server = root / "llama-server"
                model.write_bytes(b"model")
                server.write_bytes(b"server")
                wrapper.MODEL_PATH = str(model)
                wrapper.SERVER = str(server)
                wrapper.MODEL_SHA = hashlib.sha256(b"model").hexdigest()
                wrapper.BINARY_SHA = hashlib.sha256(b"server").hexdigest()
                with mock.patch.object(wrapper, "_pinned_file", return_value=True):
                    wrapper._check_pins()
                (root / wrapper.EXCLUDED[0]).write_text("forbidden")
                with self.assertRaisesRegex(wrapper.GuestError, "excluded"):
                    with mock.patch.object(wrapper, "_pinned_file", return_value=True):
                        wrapper._check_pins()
            finally:
                wrapper.PINS = old_pins
                wrapper.RUNTIME_ROOT = old_root
                wrapper.MODEL_PATH, wrapper.SERVER = old_model, old_server
                wrapper.MODEL_SHA, wrapper.BINARY_SHA = old_model_sha, old_binary_sha

    def test_runtime_custody_rejects_mode_and_symlink_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runtime.py"
            path.write_text("source")
            path.chmod(0o600)
            digest = hashlib.sha256(b"source").hexdigest()
            self.assertFalse(wrapper._pinned_file(path, digest, 0o644))
            path.unlink()
            target = Path(tmp) / "target.py"
            target.write_text("source")
            path.symlink_to(target)
            self.assertFalse(wrapper._pinned_file(path, digest, 0o644))

    def test_private_runtime_is_traversable_by_ollama_and_key_is_private(self):
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(wrapper.shutil, "chown") as chown:
            root = Path(tmp) / "private"
            key_path, key = wrapper._prepare_private_runtime(root)
            self.assertTrue(os.access(root, os.X_OK))
            self.assertEqual(root.stat().st_mode & 0o777, 0o700)
            self.assertEqual(key_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len(key), 64)
            chown.assert_any_call(root, user="ollama", group="ollama")
            chown.assert_any_call(key_path, user="ollama", group="ollama")
            wrapper._cleanup_private_runtime(root, key_path)
            self.assertFalse(root.exists())

    def test_production_must_be_masked_before_launch(self):
        args = dict(profile=wrapper.PROFILE, port=wrapper.PORT,
                    requests=wrapper.REQUESTS,
                    per_request_timeout=wrapper.PER_REQUEST_TIMEOUT,
                    deadline=wrapper.DEADLINE, lease_id="lease-1", generation=2,
                    scope_unit=wrapper._scope_unit("lease-1", 2))
        with mock.patch.object(wrapper.os, "geteuid", return_value=0), \
             self.assertRaisesRegex(wrapper.GuestError, "masked"):
            wrapper.run(**args, production_check=lambda: False)

    def test_scope_cleanup_failure_and_loaded_scope_fail_closed(self):
        class Process:
            pid = 1
            def poll(self): return 0

        def failing_runner(*args, **kwargs):
            return mock.Mock(returncode=1, stdout="", stderr="permission denied")

        with self.assertRaisesRegex(wrapper.GuestError, "scope stop"):
            wrapper._stop("scope", Process(), runner=failing_runner)

        def loaded_runner(command, **kwargs):
            if command[1] == "stop":
                return mock.Mock(returncode=0, stdout="", stderr="")
            return mock.Mock(returncode=0, stdout="loaded\n", stderr="")

        with self.assertRaisesRegex(wrapper.GuestError, "remains loaded"):
            wrapper._stop("scope", Process(), runner=loaded_runner)

    def test_scope_stop_failure_still_kills_listener(self):
        class Process:
            pid = 44
            alive = True
            def poll(self): return None if self.alive else 0
            def wait(self, timeout=None): self.alive = False

        process = Process()
        calls = []

        def runner(command, **kwargs):
            if command[1] == "stop":
                return mock.Mock(returncode=1, stdout="", stderr="permission denied")
            return mock.Mock(returncode=1, stdout="not-found\n", stderr="")

        with mock.patch.object(wrapper.os, "killpg", side_effect=lambda pid, sig: calls.append((pid, sig))):
            with self.assertRaisesRegex(wrapper.GuestError, "scope stop"):
                wrapper._stop("scope", process, runner=runner)
        self.assertEqual(calls[0][0], 44)
        self.assertFalse(process.alive)

    def test_credential_cleanup_does_not_ignore_residual_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            root.mkdir()
            key_path = root / "api-key"
            key_path.write_text("secret")
            with mock.patch.object(wrapper.shutil, "rmtree"):
                with self.assertRaisesRegex(wrapper.GuestError, "credential cleanup"):
                    wrapper._cleanup_private_runtime(root, key_path)

    def test_deadline_abort_is_bounded_and_caught_type(self):
        self.assertTrue(issubclass(wrapper.DeadlineAbort, Exception))


if __name__ == "__main__":
    unittest.main()
