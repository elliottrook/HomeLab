"""Source-only proof that the old manual acquire participates in F2 lock."""
import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import lease_controller as manual
from host_exclusion import HostExclusionError, host_exclusion


class ManualArchiveExclusionTests(unittest.TestCase):
    def test_observer_lock_blocks_manual_before_effect_or_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "state"
            root.mkdir(mode=0o700)
            args = argparse.Namespace(light=True, backup_verified=True, test_window=True)
            with patch.object(manual, "ROOT", root), \
                    patch.object(manual, "CHECKPOINTS", root / "checkpoints"), \
                    patch.object(manual, "STATE", root / "lease.json"), \
                    patch.object(manual, "LOCK", root / "lease.lock"), \
                    patch.object(manual, "ensure_root", side_effect=lambda: (root / "checkpoints").mkdir(exist_ok=True)), \
                    patch.object(manual, "_acquire_locked") as effect:
                with host_exclusion(root), self.assertRaisesRegex(manual.LeaseFailure, "held"):
                    manual.acquire(args)
                effect.assert_not_called()
                self.assertFalse((root / "lease.json").exists())
                self.assertFalse((root / "lease.lock").exists())

    def test_manual_lock_blocks_observer_until_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "state"
            root.mkdir(mode=0o700)
            with patch.object(manual, "ROOT", root):
                with manual.archive_observation_exclusion():
                    with self.assertRaises(HostExclusionError):
                        with host_exclusion(root):
                            pass
                with host_exclusion(root):
                    pass

    def test_unsafe_directory_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "state"
            root.mkdir(mode=0o700)
            alias = Path(directory) / "alias"
            alias.symlink_to(root, target_is_directory=True)
            with patch.object(manual, "ROOT", alias), self.assertRaises(manual.LeaseFailure):
                with manual.archive_observation_exclusion():
                    pass
            root.chmod(0o755)
            with patch.object(manual, "ROOT", root), self.assertRaisesRegex(manual.LeaseFailure, "custody"):
                with manual.archive_observation_exclusion():
                    pass


if __name__ == "__main__":
    unittest.main()
