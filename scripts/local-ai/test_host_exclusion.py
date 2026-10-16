import os
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


if __name__ == "__main__":
    unittest.main()
