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
    "nav-left.wav": "227b863d35a6c6ea67df559b4d302706af669c6eee5ba86a47382164fdf3f0c8",
    "nav-right.wav": "227b863d35a6c6ea67df559b4d302706af669c6eee5ba86a47382164fdf3f0c8",
    "nav-up.wav": "227b863d35a6c6ea67df559b4d302706af669c6eee5ba86a47382164fdf3f0c8",
    "nav-down.wav": "227b863d35a6c6ea67df559b4d302706af669c6eee5ba86a47382164fdf3f0c8",
    "notify.wav": "57f108306b772252095811c9827dd6667c58f53e9c80f7f733976467057de6f6",
    "select.wav": "a95d8c2a2d874a0f04b5ab82fb11d0a7a1d850562849de3c86cbf1050edb2910",
    "back.wav": "33b9852ee00869cefd0040ce6a65573ec1a5606a87352917e7654d7b36348a54",
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

    def test_seven_kodi_files_resolve_to_four_canonical_sounds(self):
        paths = sorted(RESOURCES.glob("*.wav"))
        self.assertEqual(len(paths), 7)
        self.assertEqual(len({sha256(path) for path in paths}), 4)
        movement_bytes = [(RESOURCES / name).read_bytes() for name in MOVEMENT]
        self.assertTrue(all(data == movement_bytes[0] for data in movement_bytes[1:]))

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
                self.assertLess(source.getnframes() / source.getframerate(), 0.5,
                                path.name)
                samples = pcm24(source.readframes(source.getnframes()))
            self.assertEqual(samples[:2], [0, 0], path.name)
            self.assertEqual(samples[-2:], [0, 0], path.name)
            self.assertLess(max(abs(sample) for sample in samples), 300_000,
                            path.name)
            self.assertLess(max(abs(sample) for sample in samples[:96]), 200,
                            path.name)

    def test_semantic_durations_and_reversed_back(self):
        def frames(name):
            with wave.open(str(RESOURCES / name), "rb") as source:
                return source.getnframes(), source.readframes(source.getnframes())

        movement_frames, movement = frames("nav-left.wav")
        back_frames, back = frames("back.wav")
        select_frames, _ = frames("select.wav")
        boundary_frames, _ = frames("notify.wav")
        self.assertEqual(back_frames, movement_frames)
        self.assertLess(select_frames, movement_frames)
        self.assertGreater(boundary_frames, movement_frames)
        movement_stereo = [movement[index:index + 6]
                           for index in range(0, len(movement), 6)]
        self.assertEqual(back, b"".join(reversed(movement_stereo)))

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
