import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import validate_d4_candidate_h_target as target


class TargetValidationTests(unittest.TestCase):
    def test_loads_extensionless_installed_launcher(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "launcher"
            path.write_text("MARKER = 'loaded'\n")
            old = target.LAUNCHER
            try:
                target.LAUNCHER = path
                self.assertEqual(target.load_launcher().MARKER, "loaded")
            finally:
                target.LAUNCHER = old

    def test_child_probe_contains_fixed_nonsecret_boundary(self):
        source = target.child_probe_source()
        for required in (
            "os.getuid() == 977",
            "os.getgid() == 977",
            "os.getgroups() == []",
            '"ASTER_LLAMA_API_KEY" not in os.environ',
            'Path("/etc/aster/aster.env").read_bytes()',
            'output / ".fictional-custody-probe"',
        ):
            self.assertIn(required, source)
        self.assertNotIn("qwen", source.lower())
        self.assertNotIn("/v1/", source)

    def test_service_state_accepts_only_inactive_disabled_or_static(self):
        inactive = subprocess.CompletedProcess([], 0, "inactive\n", "")
        static = subprocess.CompletedProcess([], 1, "static\n", "")
        with mock.patch.object(target.subprocess, "run", side_effect=[inactive, static]):
            self.assertEqual(target.service_state(), ("inactive", "static"))
        active = subprocess.CompletedProcess([], 0, "active\n", "")
        with mock.patch.object(target.subprocess, "run", side_effect=[active, static]):
            with self.assertRaisesRegex(RuntimeError, "not inactive"):
                target.service_state()

    def test_validator_has_no_model_or_credential_reader_import(self):
        source = Path(target.__file__).read_text()
        self.assertNotIn("urllib", source)
        self.assertNotIn("read_key_bytes(", source)
        self.assertNotIn("ASTER_LLAMA_API_KEY=", source)


if __name__ == "__main__":
    unittest.main()
