import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "static/remote"
HTML = (ROOT / "index.html").read_text()
JS = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()
SW = (ROOT / "sw.js").read_text()


class RemoteStaticTests(unittest.TestCase):
    def test_manifest_is_installable_and_scoped(self):
        manifest = json.loads((ROOT / "manifest.webmanifest").read_text())
        self.assertEqual(manifest["start_url"], "/remote/")
        self.assertEqual(manifest["scope"], "/remote/")
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["icons"][0]["src"], "/aster-app-icon.png")

    def test_shell_has_remote_keyboard_search_and_accessibility(self):
        for value in (
            'id="touchpad"', 'data-action="nav.select"',
            'id="searchForm"', 'id="textForm"', 'id="voice"',
            'data-action="text.backspace"', 'data-action="text.clear"',
            'data-action="text.cancel"', 'data-action="text.enter"',
            'role="alert"', 'aria-label="Directional controls"',
        ):
            self.assertIn(value, HTML)

    def test_equipment_controls_are_explicitly_unavailable(self):
        self.assertIn("M7 equipment bridge", HTML)
        self.assertEqual(HTML.count(" disabled>"), 4)
        for action in ("volume.up", "volume.down", "mute", "power"):
            self.assertNotIn("data-action=\"" + action + "\"", HTML)

    def test_session_is_short_lived_and_content_is_not_persisted(self):
        self.assertIn("sessionStorage.setItem('aster_remote_access_token'", JS)
        self.assertNotIn("localStorage", JS)
        self.assertNotIn("refresh_token", JS)
        self.assertNotIn("caches.open", JS)
        self.assertNotIn("console.log", JS)
        self.assertIn("$('#text').value = ''", JS)
        self.assertIn("$('#search').value = ''", JS)

    def test_voice_uses_bounded_british_media_profile(self):
        self.assertIn("form.append('profile', 'en-GB-media')", JS)

    def test_service_worker_caches_only_static_shell(self):
        self.assertIn("const SHELL =", SW)
        self.assertNotIn("/v1/", SW)
        self.assertNotIn("/voice/", SW)
        self.assertNotIn("Authorization", SW)
        self.assertIn("event.request.method !== 'GET'", SW)

    def test_astertv_palette_has_no_discarded_blue(self):
        for value in ("--brown:", "--cream:", "--gold:", "--green:"):
            self.assertIn(value, CSS)
        for value in ("#2563eb", "#1e3a5f", "--ui-accent"):
            self.assertNotIn(value, CSS)


if __name__ == "__main__":
    unittest.main()
