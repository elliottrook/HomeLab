import importlib.util
import json
from pathlib import Path
import unittest


path = Path(__file__).with_name('repair.py')
spec = importlib.util.spec_from_file_location('media_lifecycle_repair', path)
repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair)


LIBRARY = """        for source in rows:
            if not isinstance(source, dict):
                continue
            resume = source.get('resume')
"""
NEXT = """    rows = sorted((row for row in episodes if row.get('season', 0) > 0
                   and row.get('episode', 0) > 0 and order(row) > order(current)), key=order)
                    result = rpc('VideoLibrary.GetEpisodes', tvshowid=current['tvshowid'],
                                 properties=['season','episode','file','firstaired','showtitle'],
"""


class RepairTests(unittest.TestCase):
    def test_continue_watching_rejects_played_and_malformed_state(self):
        patched = repair.patch_library(LIBRARY)
        self.assertIn("if type(playcount) is not int or playcount > 0", patched)
        self.assertLess(patched.index('playcount ='), patched.index("resume ="))

    def test_manual_next_requests_and_rejects_watched_episodes(self):
        patched = repair.patch_next(NEXT)
        self.assertIn("row.get('playcount', 0) == 0", patched)
        self.assertIn("'showtitle','playcount'", patched)

    def test_payload_repins_guard_manifest_and_family(self):
        player = ("GUARDS={'skin.asterhome/tools/next_episode.py':'" +
                  repair.EXPECTED[repair.NEXT] + "'}\n").encode()
        manifest = repair.encoded({'files': [{
            'path': 'resources/lib/movie_player.py', 'bytes': len(player),
            'sha256': repair.EXPECTED[repair.PLAYER]}]})
        family = repair.encoded({'components': {'aster-global-search-ui22': {
            'files': 1, 'manifest_sha256': repair.EXPECTED[repair.MANIFEST]}}})
        originals = {
            repair.LIBRARY: LIBRARY.encode(), repair.NEXT: NEXT.encode(),
            repair.PLAYER: player, repair.MANIFEST: manifest, repair.FAMILY: family,
        }
        payload = repair.candidates(originals)
        self.assertIn(repair.sha(payload[repair.NEXT]).encode(), payload[repair.PLAYER])
        row = json.loads(payload[repair.MANIFEST])['files'][0]
        self.assertEqual(row['sha256'], repair.sha(payload[repair.PLAYER]))
        component = json.loads(payload[repair.FAMILY])['components']['aster-global-search-ui22']
        self.assertEqual(component['manifest_sha256'], repair.sha(payload[repair.MANIFEST]))

    def test_transforms_fail_closed_on_drift(self):
        with self.assertRaises(ValueError):
            repair.patch_library(LIBRARY.replace("resume =", "bookmark ="))
        with self.assertRaises(ValueError):
            repair.patch_next(NEXT.replace("showtitle", "series"))

    def test_stop_path_accepts_only_a_fully_dead_kodi_process(self):
        source = path.read_text()
        self.assertIn("['systemctl', 'stop', 'kodi'], check=False", source)
        self.assertIn("['pgrep', '-x', 'kodi.bin']", source)
        self.assertIn("raise RuntimeError('kodi-process-remains-after-stop')", source)

    def test_intro_skipper_repair_preserves_container_ownership(self):
        plugin = path.with_name('repair_jellyfin_intro_skipper.py').read_text()
        self.assertIn('owner = OLD.stat()', plugin)
        self.assertIn('os.chown(path, owner.st_uid, owner.st_gid)', plugin)


if __name__ == '__main__':
    unittest.main()
