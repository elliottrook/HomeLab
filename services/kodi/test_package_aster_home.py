import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET

import package_aster_home as release


class ReleasePackageTests(unittest.TestCase):
    def test_build_is_deterministic_and_excludes_development_files(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = release.build(Path(first))
            two = release.build(Path(second))
            self.assertEqual(
                [(item["archive"], item["sha256"]) for item in one["archives"]],
                [(item["archive"], item["sha256"]) for item in two["archives"]])
            for item in one["archives"]:
                with zipfile.ZipFile(Path(first) / item["archive"]) as archive:
                    names = archive.namelist()
                    descriptor = item["addon_id"] + "/addon.xml"
                    self.assertIn(descriptor, names)
                    addon = ET.fromstring(archive.read(descriptor))
                    self.assertEqual(addon.attrib["id"], item["addon_id"])
                    self.assertEqual(addon.attrib["version"], release.RELEASE)
                    self.assertFalse(any("/test_" in name for name in names))
                    self.assertFalse(any("/tools/install_" in name for name in names))
                    self.assertFalse(any(name.endswith(".svg") for name in names))
                    self.assertFalse(any("/__pycache__/" in name for name in names))
            manifest = json.loads((Path(first) /
                                   f"aster-home-v{release.RELEASE}-manifest.json").read_text())
            self.assertEqual(manifest["status"],
                             "production-candidate-pending-physical-libreelec-gate")
            self.assertEqual(manifest["external_dependencies"], [
                {"addon_id": "plugin.video.youtube", "version": "7.4.4",
                 "source": "Kodi Omega repository"}
            ])
            self.assertEqual(len(manifest["client_files"]), 1)
            keymap = manifest["client_files"][0]
            self.assertEqual(keymap["file"], "g20s-pro-plus.xml")
            self.assertEqual(keymap["install_target"],
                             "userdata/keymaps/g20s-pro-plus.xml")
            self.assertEqual(
                keymap["sha256"],
                release.sha256(Path(first) / keymap["file"]),
            )
            keymap_xml = ET.parse(Path(first) / keymap["file"])
            self.assertEqual(
                keymap_xml.findtext("./global/keyboard/select"),
                "RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)",
            )
            self.assertEqual(
                keymap_xml.findtext("./FullscreenVideo/keyboard/select"),
                "OSD",
            )

    def test_nonempty_output_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "existing").write_text("keep")
            with self.assertRaisesRegex(ValueError, "not empty"):
                release.build(Path(directory))

    def test_tracked_release_record_matches_rebuilt_archives(self):
        record = json.loads((Path(__file__).parent / "releases" /
                             f"aster-home-v{release.RELEASE}.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            rebuilt = release.build(Path(directory))
            rebuilt_manifest = (Path(directory) /
                                f"aster-home-v{release.RELEASE}-manifest.json")
            self.assertEqual(release.sha256(rebuilt_manifest),
                             record["manifest_sha256"])
        expected = {item["addon_id"]: (item["sha256"], item["bytes"])
                    for item in record["artifacts"]}
        actual = {item["addon_id"]: (item["sha256"], item["bytes"])
                  for item in rebuilt["archives"]}
        self.assertEqual(actual, expected)
        self.assertEqual(rebuilt["client_files"], record["client_files"])


if __name__ == "__main__":
    unittest.main()
