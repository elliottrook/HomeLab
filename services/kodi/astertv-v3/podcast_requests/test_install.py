import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("podcast_apply", ROOT / "apply_jen_podcast_requests.py")
APPLY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(APPLY)


class PodcastInstallTests(unittest.TestCase):
    def test_skin_patch_is_idempotent_and_bounded(self):
        includes = (ROOT.parent.parent / "astertv-v2/reconciliation/payload/skin.asterhome/1080i/IncludesBooks.xml")
        podcasts = (ROOT.parent.parent / "astertv-v2/reconciliation/payload/skin.asterhome/1080i/custom_1120_podcasts.xml")
        patched = APPLY.patch_includes(includes.read_bytes())
        ET.fromstring(patched)
        self.assertEqual(APPLY.patch_includes(patched), patched)
        text = patched.decode()
        self.assertEqual(text.count('id="303"'), 1)
        self.assertIn("RunAddon(script.astertv.podcast.requests)", text)
        self.assertIn("$PARAM[requestdown]", text)
        podcast_patch = APPLY.patch_podcasts(podcasts.read_bytes())
        ET.fromstring(podcast_patch)
        self.assertEqual(APPLY.patch_podcasts(podcast_patch), podcast_patch)
        self.assertIn('<param name="requestdown" value="303" />', podcast_patch.decode())

    def test_runtime_has_no_subscription_executor(self):
        source = "\n".join(path.read_text() for path in
                           (ROOT / "addon/script.astertv.podcast.requests").glob("*.py"))
        for forbidden in ("/api/items", "socket.gethostbyname", "subprocess", "feed_url"):
            self.assertNotIn(forbidden, source)
        self.assertIn("pending owner approval", source.lower())

    def test_addon_metadata_and_window_are_valid_xml(self):
        addon = ROOT / "addon/script.astertv.podcast.requests"
        ET.parse(addon / "addon.xml")
        ET.parse(addon / "resources/skins/Default/1080i/PodcastRequests.xml")
        default = (addon / "default.py").read_text()
        self.assertIn('WindowXMLDialog', default)
        self.assertIn('Dialog().yesno', default)
        self.assertIn('xbmcvfs.translatePath', default)
        self.assertNotIn('xbmc.translatePath', default)


if __name__ == "__main__":
    unittest.main()
