import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "static/remote"
AGENT = (ROOT.parent.parent / "aster_remote.py").read_text()
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
        self.assertEqual(manifest["icons"][0]["src"], "/remote/astertv-remote-512.png")
        self.assertEqual(manifest["icons"][0]["sizes"], "512x512")
        self.assertIn('/remote/astertv-remote-180.png', HTML)

    def test_shell_has_remote_keyboard_search_and_accessibility(self):
        for value in (
            'id="touchpad"', 'data-action="nav.select"',
            'id="searchForm"', 'id="textForm"', 'id="voice"',
            'data-action="text.backspace"', 'data-action="text.clear"',
            'data-action="text.cancel"', 'data-action="text.enter"',
            'role="alert"', 'aria-label="Directional controls"',
        ):
            self.assertIn(value, HTML)

    def test_approved_touch_first_shell_preserves_controls_without_captions(self):
        for value in (
            'class="search-strip"', 'class="control-panel"',
            'class="room-target"', 'id="roomLabel"',
            'id="moreOpen"', 'id="moreSheet"', 'id="moreClose"',
            'aria-label="Back"', 'aria-label="Home"',
            'aria-label="Play or pause"', 'aria-label="More controls"',
        ):
            self.assertIn(value, HTML)
        for caption in (">Back</button>", ">Home</button>", ">Play / Pause</button>", ">More</button>"):
            self.assertNotIn(caption, HTML)
        self.assertIn("moreSheet.hidden = !open", JS)
        self.assertIn("$('#roomLabel').textContent", JS)

    def test_touch_surface_blends_beneath_search_and_uses_aster_palette(self):
        self.assertIn("margin:6px 0 -13px", CSS)
        self.assertIn("radial-gradient(ellipse at 50% 43%", CSS)
        self.assertIn("rgba(243,236,223,.27)", CSS)
        self.assertIn("const CACHE = 'aster-remote-shell-v9'", SW)
        self.assertIn("self.skipWaiting()", SW)
        self.assertIn("self.clients.claim()", SW)

    def test_approved_identity_connection_and_voice_language(self):
        self.assertIn('/remote/aster-compass.png', HTML)
        self.assertIn('class="brand-name">AsterTV</h1>', HTML)
        self.assertNotIn('<img src="/aster-app-icon.png" alt="" width="42"', HTML)
        self.assertIn('class="status disconnected" role="status" aria-label="Disconnected"', HTML)
        self.assertNotIn('>Disconnected</span>', HTML)
        self.assertEqual(HTML.count('class="voice-wave"'), 1)
        self.assertEqual(HTML.count('<span class="voice-wave"'), 1)
        self.assertEqual(HTML.count('<i></i>'), 5)
        self.assertIn('.search-icon.recording .voice-wave i', CSS)
        self.assertIn('@keyframes listen-wave', CSS)

    def test_room_equipment_is_grouped_and_defaults_disabled(self):
        self.assertIn('class="volume-cluster"', HTML)
        self.assertIn('class="power-control" disabled aria-label="Power"', HTML)
        for label in ('Volume down', 'Mute', 'Volume up', 'Power'):
            self.assertIn(f'aria-label="{label}"', HTML)
        self.assertEqual(HTML.count(' disabled aria-label='), 4)
        self.assertNotIn('id="now"', HTML)
        self.assertIn('connection.setAttribute(\'aria-label\'', JS)
        self.assertNotIn("connection.textContent", JS)
        self.assertIn("'/remote/aster-compass.png'", SW)
        self.assertIn("'/remote/astertv-remote-180.png'", SW)
        self.assertIn("'/remote/astertv-remote-512.png'", SW)
        self.assertNotIn("'/aster-app-icon.png'", SW)

    def test_equipment_controls_require_live_capability_state(self):
        self.assertIn("Equipment controls unavailable for this room", HTML)
        self.assertEqual(HTML.count(" disabled aria-label="), 4)
        for action in ("equipment.volume_up", "equipment.volume_down",
                       "equipment.mute_on", "equipment.power_on"):
            self.assertIn(action, JS)
        self.assertIn("delete button.dataset.action", JS)
        self.assertIn("equipment.connected", JS)
        self.assertIn("Number.isFinite(equipment.volume_level)", JS)
        self.assertIn("typeof equipment.muted === 'boolean'", JS)

    def test_browser_uses_network_authorization_and_only_room_preference_is_persisted(self):
        self.assertNotIn("sessionStorage", JS)
        self.assertIn("const ROOM_PREFERENCE_KEY = 'aster_remote_last_room_v1'", JS)
        self.assertIn("localStorage.getItem(ROOM_PREFERENCE_KEY)", JS)
        self.assertIn("localStorage.setItem(ROOM_PREFERENCE_KEY, roomId)", JS)
        self.assertIn("rooms.some(item => item.room_id === roomId)", JS)
        self.assertNotIn("localStorage.setItem('search", JS)
        self.assertNotIn("localStorage.setItem('text", JS)
        self.assertNotIn("localStorage.setItem('voice", JS)
        self.assertNotIn("localStorage.setItem('token", JS)
        self.assertNotIn("refresh_token", JS)
        self.assertNotIn("auth.elliottrook.com", JS)
        self.assertIn("history.replaceState({}, '', '/remote/')", JS)
        self.assertIn("'controllerchange'", JS)
        self.assertNotIn('id="login"', HTML)
        self.assertNotIn('id="signOut"', HTML)
        self.assertNotIn("caches.open", JS)
        self.assertNotIn("console.log", JS)
        self.assertIn("inputDirty = false", JS)
        self.assertNotIn("$('#search').value = ''", JS)

    def test_last_valid_room_is_restored_and_stale_room_fails_safe(self):
        self.assertIn("selectedRoom || roomPreference() || select.value", JS)
        self.assertIn("rooms.some(item => item.room_id === prior) ? prior", JS)
        self.assertIn("(rooms[0]?.room_id || '')", JS)
        self.assertIn("if (selectedRoom) rememberRoom(selectedRoom)", JS)
        self.assertIn("selectedRoom = event.target.value; rememberRoom(selectedRoom)", JS)

    def test_voice_uses_bounded_british_media_profile(self):
        self.assertIn("form.append('profile', 'en-GB-media')", JS)
        self.assertIn("fetch('/v1/remote/voice'", JS)
        self.assertNotIn("Authorization", JS)
        self.assertIn("$('#search').value = heard", JS)
        self.assertNotIn("send('voice.search', heard)", JS)

    def test_voice_defaults_to_canonical_mac_authority(self):
        self.assertIn(
            'CANONICAL_VOICE_URL = "https://aster.elliottrook.com/voice/v3/v1/stt"',
            AGENT,
        )
        self.assertNotIn("192.168.70.14:9130", AGENT)

    def test_search_and_kodi_text_are_editable_not_blind_send(self):
        self.assertIn("replace(/[.!?,;:]+$/u, '')", JS)
        self.assertIn("active?.input", JS)
        self.assertIn("field.value = input.sensitive ? '' : input.value", JS)
        self.assertIn("send('text.replace', value)", JS)
        self.assertIn('id="keyboardIdle"', HTML)
        self.assertIn('id="textForm" class="keyboard-form" hidden', HTML)
        self.assertIn('>Update</button>', HTML)
        self.assertNotIn('>Send</button>', HTML)

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
