from pathlib import Path
import tempfile
import unittest
from unittest import mock

from mac.scripts.verify_runtime import RuntimeVerificationError, RUNTIMES, verify


class RuntimeVerificationTests(unittest.TestCase):
    def make_runtime(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for binary_name, contract in RUNTIMES.items():
            binary = root / "bin" / binary_name
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_bytes(b"binary")
            library_root = root / "lib" / str(contract["directory"])
            library_root.mkdir(parents=True, exist_ok=True)
            for library in contract["libraries"]:
                (library_root / library).write_bytes(b"library")
        return root

    @mock.patch("mac.scripts.verify_runtime._dependencies")
    @mock.patch("mac.scripts.verify_runtime._rpaths")
    def test_accepts_two_isolated_complete_runtimes(self, rpaths, dependencies):
        root = self.make_runtime()
        rpaths.side_effect = lambda path: [RUNTIMES[path.name]["rpath"]]
        dependencies.return_value = ["/usr/lib/libSystem.B.dylib"]
        verify(root)

    @mock.patch("mac.scripts.verify_runtime._dependencies", return_value=[])
    @mock.patch("mac.scripts.verify_runtime._rpaths")
    def test_rejects_temporary_rpath(self, rpaths, _dependencies):
        root = self.make_runtime()
        rpaths.return_value = ["/private/tmp/old-build"]
        with self.assertRaises(RuntimeVerificationError):
            verify(root)

    @mock.patch("mac.scripts.verify_runtime._dependencies", return_value=[])
    @mock.patch("mac.scripts.verify_runtime._rpaths")
    def test_rejects_missing_or_extra_library(self, rpaths, _dependencies):
        root = self.make_runtime()
        rpaths.side_effect = lambda path: [RUNTIMES[path.name]["rpath"]]
        (root / "lib" / "qwen" / "unexpected.dylib").write_bytes(b"unexpected")
        with self.assertRaises(RuntimeVerificationError):
            verify(root)


if __name__ == "__main__":
    unittest.main()
