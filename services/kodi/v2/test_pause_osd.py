import importlib.util
from pathlib import Path
import unittest
import sys
import tempfile
import types
from unittest.mock import patch
from build_pause_osd import build

spec = importlib.util.spec_from_file_location('pause_osd', Path(__file__).parent.parent / 'service.aster.playerui/service.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PauseOSDTests(unittest.TestCase):
    def setUp(self):
        self.c = module.PauseOSD()
        self.state = dict(video=True, paused=False, fullscreen=True, osd=False, blocked=False, idle=True, now=0)

    def tick(self, **changes):
        self.state.update(changes)
        return self.c.step(**self.state)

    def test_pause_edge_once(self):
        self.assertEqual(self.tick(paused=True), 'open')
        self.assertIsNone(self.tick(osd=True, now=10))
        self.assertIsNone(self.tick(now=100))

    def test_resume_hides_after_grace(self):
        self.tick(paused=True)
        self.assertIsNone(self.tick(paused=False, osd=True, now=1))
        self.assertIsNone(self.tick(now=3.9))
        self.assertEqual(self.tick(now=4), 'close')
        self.assertIsNone(self.tick(now=5))

    def test_manual_dismissal_not_reopened_or_later_closed(self):
        self.tick(paused=True)
        self.tick(osd=True)
        self.assertIsNone(self.tick(osd=False))
        self.assertIsNone(self.tick(osd=True, paused=False, now=20))
        self.assertIsNone(self.tick(now=30))

    def test_stream_menu_keeps_focus_and_resets_grace(self):
        self.tick(paused=True)
        self.tick(osd=True, paused=False, now=1)
        self.assertIsNone(self.tick(blocked=True, now=10))
        self.assertIsNone(self.tick(blocked=False, now=12))
        self.assertEqual(self.tick(now=13), 'close')

    def test_pause_inside_modal_never_steals_focus(self):
        self.assertIsNone(self.tick(blocked=True, paused=True))
        self.assertIsNone(self.tick(blocked=False, now=10))

    def test_remote_activity_extends_hide(self):
        self.tick(paused=True)
        self.tick(osd=True, paused=False, now=1)
        self.assertIsNone(self.tick(idle=False, now=4))
        self.assertIsNone(self.tick(idle=True, now=6))
        self.assertEqual(self.tick(now=7), 'close')

    def test_audio_background_other_skin_and_stop_do_nothing(self):
        for field in ('video', 'fullscreen', 'aster'):
            c = module.PauseOSD()
            state = dict(self.state, paused=True, **{field:False})
            self.assertIsNone(c.step(**state))

    def test_existing_osd_not_toggled(self):
        self.assertIsNone(self.tick(osd=True, paused=True))
        self.assertTrue(self.c.managed)

    def test_repeated_pause_resume(self):
        self.assertEqual(self.tick(paused=True), 'open')
        self.tick(osd=True, paused=False)
        self.assertIsNone(self.tick(paused=True, now=2))
        self.assertIsNone(self.tick(now=10))
        self.tick(paused=False, now=11)
        self.assertEqual(self.tick(now=14), 'close')


class PauseDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.active = False
        self.players = []
        tools = Path(__file__).parent / 'tools'
        self.xbmc = types.SimpleNamespace(executebuiltin=lambda action:None, sleep=lambda ms:None)
        with patch.dict(sys.modules, xbmc=self.xbmc):
            base_spec = importlib.util.spec_from_file_location('deploy_startup', tools / 'deploy_startup.py')
            self.base = importlib.util.module_from_spec(base_spec)
            base_spec.loader.exec_module(self.base)
            with patch.dict(sys.modules, deploy_startup=self.base):
                s = importlib.util.spec_from_file_location('deploy_pause_test', tools / 'deploy_pause_osd.py')
                self.m = importlib.util.module_from_spec(s)
                s.loader.exec_module(self.m)
        self.m.BASE = root / 'stage'
        build(self.m.BASE)
        for name in ('deploy_startup.py', 'deploy_pause_osd.py'):
            (self.m.BASE / name).write_bytes((tools / name).read_bytes())
        self.m.LIVE = root / 'live/service.aster.playerui'
        self.m.LIVE.parent.mkdir()
        self.m.CHECKPOINT = root / 'checkpoint'
        self.base.NAV = root / 'navigation'
        self.base.NAV.mkdir()
        (self.base.NAV / 'sounds.xml').write_text('<sounds/>')
        self.base.rpc = self.rpc
        guard = patch.object(self.m.os, 'uname', return_value=types.SimpleNamespace(nodename='AsterTV'))
        guard.start()
        self.addCleanup(guard.stop)

    def rpc(self, method, params=None):
        if method == 'Player.GetActivePlayers': return self.players
        if method == 'Playlist.GetItems': return dict(limits=dict(total=0))
        if method == 'Settings.GetSettings': return dict(settings=[dict(id='unchanged', value=True)])
        if method == 'Addons.GetAddonDetails': return dict(addon=dict(enabled=self.active))
        if method == 'Addons.SetAddonEnabled':
            if params['addonid'] != 'service.aster.playerui': raise ValueError('wrong-addon')
            self.active = params['enabled']
            return 'OK'
        raise ValueError('unexpected-method')

    def test_install_verify_retained_rollback(self):
        self.assertTrue(self.m.main('deploy')['ok'])
        self.assertTrue(self.m.main('verify')['ok'])
        self.assertTrue(self.m.main('rollback')['ok'])
        self.assertFalse(self.m.LIVE.exists())
        self.assertTrue((self.m.CHECKPOINT / 'disabled-addon/service.py').exists())

    def test_production_refused(self):
        with patch.object(self.m.os, 'uname', return_value=types.SimpleNamespace(nodename='AsterTVProd')):
            with self.assertRaisesRegex(RuntimeError, 'hp-only'): self.m.main('deploy')
        self.assertFalse(self.m.CHECKPOINT.exists())

    def test_playback_refused(self):
        self.players = [dict(playerid=1)]
        with self.assertRaisesRegex(RuntimeError, 'idle-empty'): self.m.main('deploy')

    def test_file_drift_refused(self):
        (self.m.BASE / 'service.aster.playerui/service.py').write_text('drift')
        with self.assertRaisesRegex(RuntimeError, 'file-drift'): self.m.main('deploy')
        self.assertFalse(self.m.CHECKPOINT.exists())


if __name__ == '__main__': unittest.main()
