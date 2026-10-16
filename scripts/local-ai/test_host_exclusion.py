import os
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

from host_exclusion import HostExclusionError, host_exclusion


class HostExclusionTests(unittest.TestCase):
    def test_second_entry_refuses_while_first_holds_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with host_exclusion(root):
                with self.assertRaisesRegex(HostExclusionError, "held"):
                    with host_exclusion(root):
                        self.fail("second entrant obtained the same host lock")
            with host_exclusion(root):
                pass

    def test_insecure_or_symlinked_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            root = parent / "state"
            root.mkdir(mode=0o700)
            alias = parent / "alias"
            alias.symlink_to(root, target_is_directory=True)
            with self.assertRaises(HostExclusionError):
                with host_exclusion(alias):
                    pass
            os.chmod(root, 0o755)
            with self.assertRaisesRegex(HostExclusionError, "custody"):
                with host_exclusion(root):
                    pass

    def test_two_install_roots_share_the_same_directory_lock(self):
        source = Path(__file__).with_name("host_exclusion.py")
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            root = parent / "state"
            root.mkdir(mode=0o700)
            modules = []
            for index in (1, 2):
                target = parent / f"module-{index}" / "host_exclusion.py"
                target.parent.mkdir()
                shutil.copyfile(source, target)
                spec = importlib.util.spec_from_file_location(f"host_exclusion_copy_{index}", target)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                modules.append(module)
            with modules[0].host_exclusion(root):
                with self.assertRaises(modules[1].HostExclusionError):
                    with modules[1].host_exclusion(root):
                        self.fail("second install root obtained the host lock")
            with modules[1].host_exclusion(root):
                pass


if __name__ == "__main__":
    unittest.main()
