import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from recovery_policy import PlaybackState, may_clear_trial_recovery
import release_guard


class RecoveryPolicyTests(unittest.TestCase):
    def test_requires_three_stable_idle_empty_samples(self):
        state = PlaybackState(0, 0, 0)
        self.assertFalse(may_clear_trial_recovery("required", state, 2))
        self.assertTrue(may_clear_trial_recovery("required", state, 3))

    def test_never_clears_with_player_or_queue(self):
        for state in (PlaybackState(1, 0, 0), PlaybackState(0, 1, 0),
                      PlaybackState(0, 0, 1)):
            self.assertFalse(may_clear_trial_recovery("required", state, 99))

    def test_never_clears_an_unset_or_unknown_flag(self):
        state = PlaybackState(0, 0, 0)
        self.assertFalse(may_clear_trial_recovery("", state, 3))
        self.assertFalse(may_clear_trial_recovery("unexpected", state, 3))


class ReleaseGuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.root = self.base / "addons"
        self.state = self.base / "accepted"
        for name in release_guard.GUARDED:
            (self.root / name).mkdir(parents=True)
            (self.root / name / "fixture.txt").write_text(name)
        (self.root / "skin.asterhome" / "Home.xml").write_text("accepted")

    def tearDown(self):
        self.temporary.cleanup()

    def test_snapshot_verify_restore_and_preserve_extra_files(self):
        accepted = release_guard.snapshot(self.root, self.state, "AsterTV-Test")
        self.assertEqual(accepted["outcome"], "accepted")
        self.assertEqual(release_guard.verify(self.root, self.state, "AsterTV-Test")["outcome"], "clean")
        target = self.root / "skin.asterhome" / "Home.xml"
        target.write_text("regressed")
        extra = self.root / "skin.asterhome" / "user-extra.txt"
        extra.write_text("keep")
        self.assertEqual(release_guard.verify(self.root, self.state, "AsterTV-Test")["outcome"], "drift")
        result = release_guard.restore(self.root, self.state, "AsterTV-Test")
        self.assertEqual(result["outcome"], "restored")
        self.assertEqual(target.read_text(), "accepted")
        self.assertEqual(extra.read_text(), "keep")

    def test_host_binding_fails_closed(self):
        release_guard.snapshot(self.root, self.state, "AsterTV-Test")
        with self.assertRaises(ValueError):
            release_guard.verify(self.root, self.state, "Wrong-Host")

    def test_corrupt_accepted_payload_fails_closed(self):
        release_guard.snapshot(self.root, self.state, "AsterTV-Test")
        payload = self.state / "payload" / "skin.asterhome" / "Home.xml"
        payload.write_text("corrupt")
        with self.assertRaises(ValueError):
            release_guard.restore(self.root, self.state, "AsterTV-Test")

    def test_incomplete_runtime_cannot_be_accepted(self):
        (self.root / "script.asterruntime").rename(self.root / "runtime.missing")
        with self.assertRaises(ValueError):
            release_guard.snapshot(self.root, self.state, "AsterTV-Test")


class ServiceBoundaryTests(unittest.TestCase):
    def test_service_has_no_player_or_playlist_mutations(self):
        source = (Path(__file__).parent / "service.aster.reliability" / "service.py").read_text()
        self.assertNotIn("Player.Stop", source)
        self.assertNotIn("Playlist.Clear", source)
        self.assertNotIn("Playlist.Remove", source)
        self.assertNotIn("Playlist.Add", source)

    def test_service_policy_copy_matches_tested_policy(self):
        root = (Path(__file__).parent / "recovery_policy.py").read_bytes()
        installed = (Path(__file__).parent / "service.aster.reliability" /
                     "recovery_policy.py").read_bytes()
        self.assertEqual(root, installed)


if __name__ == "__main__":
    unittest.main()
