import hashlib
from pathlib import Path
import tarfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
RELEASE = ROOT / "services/kodi/dist/astertv-v2.0.7-release-2026-10-31.tar.gz"
PREFIX = "aster-v2-package/lab-addon-snapshot/skin.asterhome/playlists/"
EXPECTED = {
    "tv-shows.xsp": "098e7e05a83c1120e6cc72f1ddacc6551da07c498f1e60430c1b8c9f543e4248",
    "movies.xsp": "db53469dd147c0078467a3f2e55defdb7c98a7bf28160f19a3ab9bfd4dd4028f",
    "archive-tv.xsp": "769501ff18bdf64b79f0d47cbbd74351298f67a53999717081003b9c3912e069",
    "archive-film.xsp": "3cd56cdf45782cbc2a2cac87c18747802efddcbf21754274a67d705cbafc5d3d",
}


class MediaLifecycleFreezeTests(unittest.TestCase):
    def test_fail_safe_playlists_remain_exact_in_immutable_v2(self):
        with tarfile.open(RELEASE, "r:gz") as archive:
            for name, expected in EXPECTED.items():
                data = archive.extractfile(PREFIX + name).read()
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected)
                self.assertIn(b'<rule field="tag" operator="is">', data)

    def test_screensaver_uses_all_four_fail_safe_routes(self):
        source = (ROOT / "services/kodi/astertv-v3/screensaver/default.py").read_text()
        for name in EXPECTED:
            self.assertIn("special://skin/playlists/" + name, source)

    def test_v3_does_not_ship_an_unapproved_replacement_playlist(self):
        v3 = ROOT / "services/kodi/astertv-v3"
        candidates = {path.name for path in v3.rglob("*.xsp")}
        self.assertEqual(candidates, set())


if __name__ == "__main__":
    unittest.main()
