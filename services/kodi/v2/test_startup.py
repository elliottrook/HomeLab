import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from build_startup import build

SERVICE = Path(__file__).parent.parent / 'service.aster.startup/service.py'


class StartupDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.enabled = False
        self.players = []
        xbmc = types.SimpleNamespace(executebuiltin=lambda action: None, sleep=lambda ms: None)
        with patch.dict(sys.modules, xbmc=xbmc):
            spec = importlib.util.spec_from_file_location('startup_deploy', SERVICE.parent.parent / 'v2/tools/deploy_startup.py')
            self.m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.m)
        self.m.BASE = root / 'stage'
        build(self.m.BASE)
        self.m.LIVE = root / 'live/service.aster.startup'
        self.m.LIVE.parent.mkdir()
        self.m.CHECKPOINT = root / 'checkpoint'
        self.m.NAV = root / 'navigation'
        self.m.NAV.mkdir()
        (self.m.NAV / 'sounds.xml').write_text('<sounds/>')
        self.m.rpc = self.rpc
        guard = patch.object(self.m.os, 'uname', return_value=types.SimpleNamespace(nodename='AsterTV'))
        guard.start()
        self.addCleanup(guard.stop)

    def rpc(self, method, params=None):
        if method == 'Player.GetActivePlayers': return self.players
        if method == 'Playlist.GetItems': return dict(limits=dict(total=0))
        if method == 'Settings.GetSettings': return dict(settings=[dict(id='audiooutput.passthrough', value=True)])
        if method == 'Addons.GetAddonDetails': return dict(addon=dict(enabled=self.enabled))
        if method == 'Addons.SetAddonEnabled':
            if params['addonid'] != 'service.aster.startup': raise ValueError('wrong-addon')
            self.enabled = params['enabled']
            return 'OK'
        raise ValueError('unexpected-rpc')

    def test_install_and_nondestructive_recovery(self):
        before = self.m.snapshot()
        self.assertTrue(self.m.main('deploy')['ok'])
        self.assertTrue(self.enabled)
        self.assertTrue(self.m.main('rollback')['ok'])
        self.assertFalse(self.enabled)
        self.assertFalse(self.m.LIVE.exists())
        self.assertTrue((self.m.CHECKPOINT / 'disabled-addon/startup.wav').exists())
        self.assertEqual(before, self.m.snapshot())

    def test_production_is_refused(self):
        with patch.object(self.m.os, 'uname', return_value=types.SimpleNamespace(nodename='AsterTVProd')):
            with self.assertRaisesRegex(RuntimeError, 'hp-only'): self.m.main('deploy')
        self.assertFalse(self.m.CHECKPOINT.exists())

    def test_playback_is_refused(self):
        self.players = [dict(playerid=1)]
        with self.assertRaisesRegex(RuntimeError, 'idle-empty'): self.m.main('deploy')
        self.assertFalse(self.m.CHECKPOINT.exists())

    def test_drift_is_refused_before_checkpoint(self):
        (self.m.BASE / 'service.aster.startup/service.py').write_text('drift')
        with self.assertRaisesRegex(RuntimeError, 'addon-file-drift'): self.m.main('deploy')
        self.assertFalse(self.m.CHECKPOINT.exists())


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / 'package'
        build(self.out)
        self.calls = []
        self.xbmc = types.SimpleNamespace(
            Monitor=lambda: types.SimpleNamespace(waitForAbort=lambda seconds: False),
            getCondVisibility=lambda condition: condition == 'Window.IsActive(home)',
            playSFX=lambda *args, **kwargs: self.calls.append((args, kwargs)),
            log=lambda *args: None, LOGINFO=1)
        vfs = types.SimpleNamespace(translatePath=lambda path: str(self.root / ('temp' if path == 'special://temp/' else 'profile')))
        (self.root / 'temp').mkdir()
        with patch.dict(sys.modules, xbmc=self.xbmc, xbmcvfs=vfs):
            spec = importlib.util.spec_from_file_location('startup_service', self.out / 'service.aster.startup/service.py')
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
        self.module.session_key = lambda: 'test-session'
        self.module.rpc = self.rpc

    def tearDown(self):
        self.tmp.cleanup()

    def rpc(self, method, params=None):
        if method == 'Player.GetActivePlayers': return []
        if method == 'Playlist.GetItems': return dict(limits=dict(total=0))
        if method == 'Settings.GetSettingValue': return dict(value='skin.asterhome')
        raise RuntimeError('unexpected-rpc')

    def test_once_per_process_and_no_player_or_settings_writes(self):
        self.assertEqual(self.module.run(), 'gui-sound-requested')
        self.assertEqual(self.module.run(), 'already-attempted')
        self.assertEqual(len(self.calls), 1)
        self.assertFalse(self.calls[0][1]['useCached'])

    def test_active_playback_skips_without_retry(self):
        original = self.rpc
        self.module.rpc = lambda method, params=None: [dict(playerid=1)] if method == 'Player.GetActivePlayers' else original(method, params)
        self.assertEqual(self.module.run(), 'playback-or-queue-skipped')
        self.module.rpc = original
        self.assertEqual(self.module.run(), 'already-attempted')
        self.assertEqual(self.calls, [])

    def test_asset_drift_fails_closed(self):
        (self.out / 'service.aster.startup/startup.wav').write_bytes(b'invalid')
        self.assertEqual(self.module.run(), 'failed-ValueError')
        self.assertEqual(self.calls, [])

    def test_shutdown_no_sound(self):
        self.xbmc.Monitor = lambda: types.SimpleNamespace(waitForAbort=lambda seconds: True)
        self.assertEqual(self.module.run(), 'shutdown')
        self.assertEqual(self.calls, [])

    def test_not_ready_times_out(self):
        self.xbmc.getCondVisibility = lambda condition: False
        self.assertEqual(self.module.run(), 'not-ready')
        self.assertEqual(self.calls, [])

    def test_builder_immutable(self):
        with self.assertRaisesRegex(ValueError, 'immutable'):
            build(self.out)

    def test_nonempty_queue_skips(self):
        original = self.rpc
        self.module.rpc = lambda method, params=None: dict(limits=dict(total=1)) if method == 'Playlist.GetItems' else original(method, params)
        self.assertEqual(self.module.run(), 'playback-or-queue-skipped')
        self.assertEqual(self.calls, [])

    def test_playback_started_during_settle_skips(self):
        reads = []
        def idle():
            reads.append(1)
            return len(reads) == 1
        self.module.idle = idle
        self.assertEqual(self.module.run(), 'readiness-changed-skipped')
        self.assertEqual(self.calls, [])

    def test_new_process_gets_its_own_single_chime(self):
        self.assertEqual(self.module.run(), 'gui-sound-requested')
        self.module.session_key = lambda: 'different-session'
        self.assertEqual(self.module.run(), 'gui-sound-requested')
        self.assertEqual(len(self.calls), 2)


if __name__ == '__main__': unittest.main()
