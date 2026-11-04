import ast
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).with_name("promote_v207_to_low_spec.py")
SPEC = importlib.util.spec_from_file_location("low_spec_promoter", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

INSTALLER_PATH = Path(__file__).with_name("install_production_addons.py")
INSTALLER_SPEC = importlib.util.spec_from_file_location("low_spec_addons", INSTALLER_PATH)
INSTALLER = importlib.util.module_from_spec(INSTALLER_SPEC)
assert INSTALLER_SPEC.loader is not None
INSTALLER_SPEC.loader.exec_module(INSTALLER)

RELIABILITY_PATH = Path(__file__).with_name("install_reliability.py")
RELIABILITY_SPEC = importlib.util.spec_from_file_location(
    "low_spec_reliability", RELIABILITY_PATH)
RELIABILITY = importlib.util.module_from_spec(RELIABILITY_SPEC)
assert RELIABILITY_SPEC.loader is not None
RELIABILITY_SPEC.loader.exec_module(RELIABILITY)


class LowSpecPromoterTests(unittest.TestCase):
    def test_wrapper_is_host_bound_and_pins_original_promoter(self):
        self.assertEqual(MODULE.TARGET_HOST, "AsterTV-Jen")
        self.assertRegex(MODULE.EXPECTED_PROMOTER_SHA256, r"^[0-9a-f]{64}$")
        tree = ast.parse(MODULE_PATH.read_text())
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        self.assertFalse(
            any(isinstance(call.func, ast.Name) and call.func.id in {"exec", "eval"} for call in calls)
        )

    def test_sha256_reads_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate"
            candidate.write_bytes(b"astertv-low-spec\n")
            self.assertEqual(
                MODULE.sha256(candidate),
                hashlib.sha256(b"astertv-low-spec\n").hexdigest(),
            )

    def test_wrong_host_fails_before_package_access(self):
        with mock.patch.object(MODULE.os, "uname") as uname:
            uname.return_value.nodename = "AsterTV-Family"
            with self.assertRaisesRegex(RuntimeError, "AsterTV-Jen host only"):
                MODULE.main()

    def test_production_dependency_closure_is_pinned(self):
        self.assertEqual(INSTALLER.EXPECTED_FILE_COUNT, 683)
        self.assertRegex(INSTALLER.EXPECTED_DIGEST, r"^[0-9a-f]{64}$")
        self.assertEqual(INSTALLER.EXPECTED["plugin.video.jellyfin"], "2.2.0+py3")
        self.assertEqual(INSTALLER.EXPECTED["plugin.video.youtube"], "7.4.4")
        self.assertEqual(INSTALLER.TARGET_HOST, "AsterTV-Jen")

    def test_reliability_adapter_pins_reviewed_installer(self):
        installer = RELIABILITY_PATH.parents[1] / "reliability" / "install.py"
        self.assertEqual(
            hashlib.sha256(installer.read_bytes()).hexdigest(),
            RELIABILITY.EXPECTED_INSTALLER_SHA256,
        )
        source = RELIABILITY_PATH.read_text()
        self.assertIn('"--allow-missing-guarded", "plugin.video.astersearch"', source)
        self.assertIn('module.ALLOWED_HOSTS = {"AsterTV-Jen"}', source)


if __name__ == "__main__":
    unittest.main()
