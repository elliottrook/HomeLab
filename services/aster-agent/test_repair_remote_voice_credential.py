import importlib.util
from pathlib import Path
import stat
import tempfile
import unittest


PATH = Path(__file__).with_name("repair_remote_voice_credential.py")
SPEC = importlib.util.spec_from_file_location("repair_remote_voice_credential", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RemoteVoiceCredentialRepairTests(unittest.TestCase):
    def test_updates_only_named_key(self):
        old = "a" * 64
        new = "b" * 64
        raw = f"ONE=unchanged\n{MODULE.KEY}={old}\nTWO=unchanged\n"
        result = MODULE.update_environment(raw, new)
        self.assertEqual(result, f"ONE=unchanged\n{MODULE.KEY}={new}\nTWO=unchanged\n")

    def test_rejects_duplicate_key(self):
        raw = f"{MODULE.KEY}={'a' * 64}\n{MODULE.KEY}={'b' * 64}\n"
        with self.assertRaisesRegex(RuntimeError, "cardinality"):
            MODULE.update_environment(raw, "c" * 64)

    def test_private_key_file_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key"
            path.write_text("c" * 64 + "\n", encoding="utf-8")
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            self.assertEqual(MODULE.replacement_key(path), "c" * 64)

    def test_rejects_group_readable_key_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key"
            path.write_text("d" * 64, encoding="utf-8")
            path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
            with self.assertRaisesRegex(RuntimeError, "mode"):
                MODULE.replacement_key(path)


if __name__ == "__main__":
    unittest.main()
