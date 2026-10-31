#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import apply_music_identity_marker_fix as subject


class MusicIdentityMarkerFixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.marker = root / "profile/normal-playback.json"
        self.marker.parent.mkdir(parents=True)
        self.checkpoints = root / "checkpoints"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_fix(self) -> None:
        uname = type("Uname", (), {"nodename": "AsterTV-Bedroom"})()
        with mock.patch.object(subject, "MARKER", self.marker), \
                mock.patch.object(subject, "CHECKPOINT_ROOT", self.checkpoints), \
                mock.patch.object(subject, "RECOVERY_GUARD",
                                  Path(self.temporary.name) / "no-recovery"), \
                mock.patch.object(subject.os, "uname", return_value=uname), \
                mock.patch("builtins.print"):
            subject.main()

    def test_migrates_legacy_bedroom_identity_and_checkpoints(self) -> None:
        original = {"enabled": True, "host": "AsterTV", "queue_limit": 20000}
        self.marker.write_text(json.dumps(original))
        self.run_fix()
        self.assertEqual(json.loads(self.marker.read_text()), {
            "enabled": True,
            "host": "AsterTV-Bedroom",
            "queue_limit": 20000,
        })
        saved = (self.checkpoints / "aster-music-identity-AsterTV-Bedroom" /
                 "normal-playback.json.before")
        self.assertEqual(json.loads(saved.read_text()), original)

    def test_rejects_an_unexpected_capability(self) -> None:
        self.marker.write_text(json.dumps({
            "enabled": False,
            "host": "AsterTV",
            "queue_limit": 20000,
        }))
        with self.assertRaisesRegex(RuntimeError, "unexpected music capability marker"):
            self.run_fix()


if __name__ == "__main__":
    unittest.main()
