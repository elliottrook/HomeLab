import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from youtube_credentials import CredentialError, configure, configured, normalize


ROOT = Path(__file__).resolve().parents[3]
SKIN = ROOT / "services/kodi/skin.asterhome"


class YouTubeCredentialTests(unittest.TestCase):
    def test_normalizes_official_json_file_client_id(self):
        values = normalize("key", "client.apps.googleusercontent.com", "secret")
        self.assertEqual(values["client_id"], "client")

    def test_preserves_developer_keys_and_configures_runtime_user_set(self):
        source = json.dumps({"keys": {"developer": {"youtube": "retained"}}}).encode()
        result = configure(source, normalize("key", "client", "secret"))
        parsed = json.loads(result)
        self.assertEqual(parsed["keys"]["developer"], {"youtube": "retained"})
        self.assertEqual(parsed["keys"]["user"], {
            "api_key": "key", "client_id": "client", "client_secret": "secret",
        })
        self.assertNotIn("personal", parsed["keys"])
        self.assertTrue(configured(result))

    def test_replaces_empty_runtime_slot_in_established_install(self):
        source = json.dumps({"keys": {
            "user": {"api_key": "", "client_id": "", "client_secret": ""},
            "personal": {"api_key": "old", "client_id": "old", "client_secret": "old"},
            "developer": {},
        }}).encode()
        result = configure(source, normalize("key", "client", "secret"))
        parsed = json.loads(result)
        self.assertEqual(parsed["keys"]["user"]["client_id"], "client")
        self.assertNotIn("personal", parsed["keys"])
        self.assertTrue(configured(result))

    def test_rejects_missing_multiline_or_invalid_existing_state(self):
        for values in (("", "id", "secret"), ("key\nleak", "id", "secret")):
            with self.assertRaises(CredentialError):
                normalize(*values)
        with self.assertRaises(CredentialError):
            configure(b"not-json", normalize("key", "id", "secret"))


class YouTubeLandingTests(unittest.TestCase):
    def test_official_addon_remains_the_only_youtube_route(self):
        launcher = (ROOT / "services/kodi/v2/media_top_rail.py").read_text()
        self.assertIn("plugin://plugin.video.youtube/", launcher)
        self.assertNotIn("youtube.com", launcher)

    def test_browse_page_has_aster_youtube_contract(self):
        browse = (SKIN / "1080i/MyVideoNav.xml").read_text()
        includes = (SKIN / "1080i/Includes.xml").read_text()
        ET.fromstring(browse)
        ET.fromstring(includes)
        self.assertIn("$VAR[AsterBrowsePlot]", browse)
        self.assertIn("$VAR[AsterBrowseSidebarHeading]", browse)
        self.assertGreaterEqual(browse.count("String.Contains(Container.FolderPath,plugin.video.youtube)"), 8)
        self.assertIn("special://skin/media/33-aster-youtube-128.png", includes)
        for forbidden in ("api_key", "client_secret", "googleusercontent.com", "youtube.com"):
            self.assertNotIn(forbidden, browse.lower())
            self.assertNotIn(forbidden, includes.lower())

    def test_supplied_asset_is_retained_exactly(self):
        import hashlib
        asset = ROOT / "docs/assets/aster-v2/SVG/33-aster-youtube.svg"
        self.assertEqual(hashlib.sha256(asset.read_bytes()).hexdigest(),
                         "449f30b8ddff8b4fa3339bd58463064955a2215731766e2f724cd94ff611a3eb")


if __name__ == "__main__":
    unittest.main()
