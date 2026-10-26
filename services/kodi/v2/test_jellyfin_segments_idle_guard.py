import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

from jellyfin_segments_idle_guard import NEEDLE,build,digest,transform
from jellyfin_segments_idle_guard_install import run

SOURCE=b'import settings\nclass C:\n    def f(self):\n'+NEEDLE+b'                pass\n'

class JellyfinSegmentsIdleGuardTests(unittest.TestCase):
    def test_transform_requires_owned_jellyfin_item(self):
        result=transform(SOURCE,hashlib.sha256(SOURCE).hexdigest()).decode()
        self.assertIn('self.player.played',result); self.assertIn('self.player.isPlaying()',result)
        self.assertIn('settings("mediaSegmentsEnabled.bool")',result)
    def test_unknown_source_refused(self):
        with self.assertRaisesRegex(ValueError,'predecessor'): transform(b'unknown')
    def test_install_verify_and_rollback(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent); storage=root/'storage'; target=storage/'.kodi/addons/plugin.video.jellyfin/jellyfin_kodi/segments.py'
            target.parent.mkdir(parents=True); target.write_bytes(SOURCE); stage=root/'stage'
            with patch('jellyfin_segments_idle_guard.BEFORE',digest(SOURCE)): pin=build(target,stage)
            with patch('jellyfin_segments_idle_guard_install.kodi_running',return_value=False):
                self.assertTrue(run('install',stage,storage,pin)['installed']); self.assertTrue(run('verify',stage,storage,pin)['active']); self.assertTrue(run('rollback',stage,storage,pin)['rolled_back'])
            self.assertEqual(target.read_bytes(),SOURCE)

if __name__=='__main__': unittest.main()
