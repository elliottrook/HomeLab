import importlib.util
from pathlib import Path
import tarfile
import unittest
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parents[1] / "dist/astertv-v2-lab-reconciled-2026-10-30-r9.tar.gz"
PREFIX = "aster-v2-package/lab-addon-snapshot/"

spec = importlib.util.spec_from_file_location(
    "acceptance_repairs", HERE / "apply_acceptance_repairs.py")
repairs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repairs)


class AcceptanceRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = tarfile.open(ARCHIVE, "r:gz")

    @classmethod
    def tearDownClass(cls):
        cls.archive.close()

    def source(self, relative):
        member = self.archive.extractfile(PREFIX + relative)
        self.assertIsNotNone(member)
        return member.read()

    def test_every_repair_is_hash_guarded_and_changes_one_member(self):
        for relative, row in repairs.REPAIRS.items():
            with self.subTest(relative=relative):
                original = self.source(relative)
                self.assertEqual(repairs.sha(original), row["before"])
                candidate = repairs.patched(relative, original)
                self.assertNotEqual(candidate, original)
                if relative.endswith(".py"):
                    compile(candidate.decode("utf-8"), relative, "exec")
                elif relative.endswith(".xml"):
                    ET.fromstring(candidate)

    def test_music_grid_returns_to_real_pill(self):
        candidate = repairs.patched(
            "skin.asterhome/1080i/custom_1113_music.xml",
            self.source("skin.asterhome/1080i/custom_1113_music.xml"),
        ).decode()
        self.assertIn('name="gridup" value="110"', candidate)
        self.assertNotIn('name="gridup" value="116"', candidate)

    def test_screensaver_has_opaque_full_screen_surface(self):
        candidate = repairs.patched(
            "screensaver.asterhome.v2lab/resources/skins/Default/1080i/AsterIdle.xml",
            self.source("screensaver.asterhome.v2lab/resources/skins/Default/1080i/AsterIdle.xml"),
        ).decode()
        self.assertIn("<backgroundcolor>ff000000</backgroundcolor>", candidate)
        self.assertIn('<width>1920</width><height>1080</height>', candidate)

    def test_custom_window_consumers_use_kodi_22_active_visibility(self):
        for relative in (
            "script.asterseerr/default.py",
            "script.astervoice.v2lab/default.py",
            "script.asterruntime/aster-camera2/view.py",
            "script.asterruntime/aster-digest-player8/default.py",
            "script.asterruntime/aster-digest-reader6/default.py",
        ):
            with self.subTest(relative=relative):
                candidate = repairs.patched(relative, self.source(relative)).decode()
                self.assertIn("Window.IsActive(", candidate)

    def test_youtube_back_restores_a_root_pill_not_async_content(self):
        candidate = repairs.patched(
            "skin.asterhome/tools/youtube_back.py",
            self.source("skin.asterhome/tools/youtube_back.py"),
        ).decode()
        self.assertIn("SetFocus(9300)", candidate)
        self.assertNotIn("SetFocus(9530)", candidate)


if __name__ == "__main__":
    unittest.main()
