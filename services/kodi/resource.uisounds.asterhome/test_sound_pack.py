import hashlib
import json
import sys
import tempfile
import unittest
import wave
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESOURCES = ROOT / "resources"
KODI_ROOT = ROOT.parent
sys.path.insert(0, str(KODI_ROOT))
import package_aster_home as release_package
MOVEMENT = ("nav-left.wav", "nav-right.wav", "nav-up.wav", "nav-down.wav")
EXPECTED_SHA256 = {
    "nav-left.wav": "233b96079ed5471e774b86f840f7ef00dabe2b6f5c5effe91d4ccb17aafb2285",
    "nav-right.wav": "dce25cc207715fba406fb86905e32c4bfbfc5ec17be83abff2db2d9cb77aaa28",
    "nav-up.wav": "08037d2c1e0dd6f930715584493f98e09885e3a8126df076a3cdf01729663cba",
    "nav-down.wav": "6c414975aff7b7d4caa8866a0e4ffa41f80f222b1c4ca5db199a45c34d741ea9",
    "notify.wav": "c093d94abbabc0383d278b9f8e39dda8ca5fbfdee8080bdce1c4078126e175c8",
    "select.wav": "6e38a7c6fc9964c8c53e49409df42d53200ce51e221c2dbb63b13a8bdb811c3f",
    "back.wav": "b5c3678e2849cb6b9dd15125f2e1ebeb9afda6f469524d6bada3a20ba6424125",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pcm24(data):
    values = []
    for offset in range(0, len(data), 3):
        value = int.from_bytes(data[offset:offset + 3], "little")
        if value & 0x800000:
            value -= 1 << 24
        values.append(value)
    return values


class SoundPackTests(unittest.TestCase):
    def test_action_map_is_complete(self):
        root = ET.parse(RESOURCES / "sounds.xml").getroot()
        actions = {
            node.findtext("name"): node.findtext("file")
            for node in root.findall("./actions/action")
        }
        self.assertEqual(set(actions), {
            "left", "right", "up", "down", "select", "parentdir",
            "previousmenu", "error",
        })
        self.assertEqual(actions["left"], "nav-left.wav")
        self.assertEqual(actions["right"], "nav-right.wav")
        self.assertEqual(actions["select"], "select.wav")
        self.assertEqual(actions["parentdir"], "back.wav")
        self.assertEqual(actions["previousmenu"], "back.wav")
        self.assertEqual(actions["error"], "notify.wav")

    def test_seven_kodi_files_are_distinct_canonical_sounds(self):
        paths = sorted(RESOURCES.glob("*.wav"))
        self.assertEqual(len(paths), 7)
        self.assertEqual(len({sha256(path) for path in paths}), 7)

    def test_canonical_hashes_are_locked(self):
        self.assertEqual(
            {path.name: sha256(path) for path in RESOURCES.glob("*.wav")},
            EXPECTED_SHA256,
        )

    def test_wavs_are_short_stereo_pcm_with_silent_edges(self):
        for path in RESOURCES.glob("*.wav"):
            with wave.open(str(path), "rb") as source:
                self.assertEqual(source.getnchannels(), 2, path.name)
                self.assertEqual(source.getsampwidth(), 3, path.name)
                self.assertEqual(source.getframerate(), 48_000, path.name)
                self.assertLess(source.getnframes() / source.getframerate(), 0.6,
                                path.name)
                samples = pcm24(source.readframes(source.getnframes()))
            self.assertEqual(samples[:2], [0, 0], path.name)
            self.assertEqual(samples[-2:], [0, 0], path.name)
            self.assertLess(max(abs(sample) for sample in samples), 300_000,
                            path.name)
            self.assertLess(max(abs(sample) for sample in samples[:96]), 200,
                            path.name)

    def test_semantic_durations(self):
        def frames(name):
            with wave.open(str(RESOURCES / name), "rb") as source:
                return source.getnframes(), source.readframes(source.getnframes())

        movement_frames, _ = frames("nav-left.wav")
        back_frames, _ = frames("back.wav")
        select_frames, _ = frames("select.wav")
        boundary_frames, _ = frames("notify.wav")
        self.assertGreater(back_frames, movement_frames)
        self.assertGreater(select_frames, movement_frames)
        self.assertGreater(boundary_frames, movement_frames)

    def test_canonical_sound_archive_matches_release_record(self):
        record = json.loads((
            KODI_ROOT / "releases" /
            "aster-canonical-ui-sounds-2026-10-25.json"
        ).read_text())
        with tempfile.TemporaryDirectory() as directory:
            built = release_package.build_archive(
                "resource.uisounds.asterhome", Path(directory)
            )
        self.assertEqual(built["archive"], Path(record["archive"]["path"]).name)
        self.assertEqual(built["bytes"], record["archive"]["bytes"])
        self.assertEqual(built["sha256"], record["archive"]["sha256"])


if __name__ == "__main__":
    unittest.main()
