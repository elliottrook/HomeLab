import os
from pathlib import Path
import tempfile
import unittest
import full_aster_first_screen_controller as controller


class ControllerBoundaryTests(unittest.TestCase):
    def test_pre_effect_cleanup_removes_only_exact_root_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = tuple(root / name for name in ("f4", "f5", "admission"))
            for path in paths:
                path.write_bytes(b"{}\n")
                path.chmod(0o600)
            controller._remove_pre_effect_files(paths, owner_uid=os.getuid())
            self.assertTrue(all(not path.exists() for path in paths))

    def test_pre_effect_cleanup_rejects_weak_mode_without_deleting(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "f4"
            path.write_bytes(b"{}\n")
            path.chmod(0o644)
            with self.assertRaises(controller.ControllerError):
                controller._remove_pre_effect_files((path,), owner_uid=os.getuid())
            self.assertTrue(path.exists())

    def test_mount_and_mapped_identity_are_fixed(self):
        self.assertEqual(controller.MOUNT_KEY, "mp0")
        self.assertIn("ro=1,backup=0", controller.MOUNT_VALUE)
        self.assertEqual((controller.MAPPED_UID, controller.MAPPED_GID),
                         (100999, 100991))


if __name__ == "__main__":
    unittest.main()
