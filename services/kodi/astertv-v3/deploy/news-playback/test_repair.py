import importlib.util
import json
import unittest
from pathlib import Path


path = Path(__file__).with_name("repair.py")
spec = importlib.util.spec_from_file_location("news_playback_repair", path)
repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair)


PORT = """def idle():
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems', dict(playlistid=i,
        limits=dict(start=0, end=1)))['limits']['total'] == 0 for i in (0, 1))

class KodiPort:
    def __init__(self):
        self.last_target = 0
    def open(self):
        if self.opened or not idle(): raise ValueError('idle-single-open-required')
        self.opened = True
        self.player.play(str(self.path))
    def owned(self):
        try:
            return (self.opened and self.player.starts == 1 and not self.player.finished
                and self.player.isPlayingAudio() and self.player.getPlayingFile() == str(self.path)
                and audio_only
                and stat.S_ISREG(meta.st_mode)
                and (meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns) == self.signature)
        except (OSError, RuntimeError): return False
"""


class RepairTests(unittest.TestCase):
    def test_repair_is_pinned_for_family_and_low_spec_hosts(self):
        self.assertEqual(set(repair.BASELINES), {"AsterTV-Family", "AsterTV-Jen"})
        for host, baselines in repair.BASELINES.items():
            self.assertEqual(set(baselines),
                             {repair.PORT, repair.MANIFEST, repair.FAMILY, repair.WRAPPER})
            self.assertTrue(all(len(value) == 64 for value in baselines.values()), host)
        self.assertNotEqual(repair.BASELINES["AsterTV-Family"][repair.PORT],
                            repair.BASELINES["AsterTV-Jen"][repair.PORT])
        self.assertNotEqual(repair.BASELINES["AsterTV-Family"][repair.MANIFEST],
                            repair.BASELINES["AsterTV-Jen"][repair.MANIFEST])

    def test_port_allows_retained_queue_but_preserves_exact_snapshot(self):
        patched = repair.patch_port(PORT)
        self.assertIn("return not rpc('Player.GetActivePlayers')", patched)
        self.assertIn("self.queue_before = queue_state()", patched)
        self.assertIn("own_audio = (1, (str(self.path),))", patched)
        self.assertIn("self.queue_unchanged()", patched)
        self.assertNotIn("queue_state() == self.queue_snapshot", patched)
        self.assertIn("end=1000", patched)
        self.assertNotIn("end=1)))['limits']['total'] == 0", patched)
        self.assertNotIn("Playlist.Clear", patched)
        self.assertNotIn("Playlist.Remove", patched)

    def test_payload_repins_player_wrapper_and_family(self):
        port = PORT.encode()
        manifest = (json.dumps({"files": [{"path": "resources/lib/digest_kodi_port.py",
                                            "bytes": len(port), "sha256": repair.sha(port)}]},
                               indent=2, sort_keys=True) + "\n").encode()
        wrapper = ("PIN = '" + repair.sha(manifest) + "'\n").encode()
        family = (json.dumps({
            "components": {"aster-digest-player8": {"manifest_sha256": repair.sha(manifest)}},
            "skin": {"tools/aster_v2_digest.py": repair.sha(wrapper)},
        }, indent=2, sort_keys=True) + "\n").encode()
        payload = repair.build_payload(port, manifest, family, wrapper)
        player = json.loads(payload[repair.MANIFEST])
        self.assertEqual(player["files"][0]["sha256"], repair.sha(payload[repair.PORT]))
        new_family = json.loads(payload[repair.FAMILY])
        self.assertEqual(new_family["components"]["aster-digest-player8"]["manifest_sha256"],
                         repair.sha(payload[repair.MANIFEST]))
        self.assertEqual(new_family["skin"]["tools/aster_v2_digest.py"],
                         repair.sha(payload[repair.WRAPPER]))

    def test_transform_fails_closed_on_drift(self):
        with self.assertRaises(ValueError):
            repair.patch_port(PORT.replace("idle-single-open-required", "changed"))


if __name__ == "__main__":
    unittest.main()
