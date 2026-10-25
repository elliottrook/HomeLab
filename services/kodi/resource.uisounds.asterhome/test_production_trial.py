"""Isolated file/RPC simulations; never connect to a Kodi box."""
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent


class ProductionTrialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        with patch.dict(sys.modules, {'xbmc': types.SimpleNamespace()}):
            spec = importlib.util.spec_from_file_location('sound_trial', ROOT / 'tools/production_soft_puff.py')
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
        m = self.module
        base = Path(self.tmp.name)
        m.BASE, m.LIVE, m.CHECKPOINT = base / 'stage', base / 'live', base / 'checkpoint'
        (m.BASE / 'resources').mkdir(parents=True)
        m.LIVE.mkdir()
        for name in m.EXPECTED:
            shutil.copyfile(ROOT / 'resources' / name, m.BASE / 'resources' / name)
            (m.LIVE / name).write_bytes(('original-' + name).encode())
        m.EXPECTED = {name: m.sha(m.LIVE / name) for name in m.EXPECTED}
        (m.LIVE / 'sounds.xml').write_text('<sounds/>')
        self.values = {'lookandfeel.soundskin': 'resource.uisounds.asterhome', 'audiooutput.passthrough': True}
        self.active = []
        self.fail_next_reload = False
        m.rpc = self.rpc
        self.host = patch.object(m.os, 'uname', return_value=types.SimpleNamespace(nodename='AsterTVProd'))
        self.host.start()
        self.addCleanup(self.host.stop)

    def rpc(self, method, params=None):
        if method == 'Settings.GetSettings':
            return {'settings': [{'id': k, 'value': v} for k, v in self.values.items()]}
        if method == 'Player.GetActivePlayers':
            return self.active
        if method == 'Settings.SetSettingValue':
            if params['value'] and self.fail_next_reload:
                self.fail_next_reload = False
                return False
            self.values[params['setting']] = params['value']
            return True
        raise RuntimeError('Unexpected RPC')

    def run_mode(self, mode):
        with patch.object(sys, 'argv', ['trial', mode]):
            return self.module.main()

    def test_deploy_and_exact_rollback(self):
        m = self.module
        self.assertTrue(self.run_mode('deploy')['installed'])
        self.assertTrue(self.run_mode('rollback')['rolled_back'])
        for name, digest in m.EXPECTED.items():
            self.assertEqual(m.sha(m.LIVE / name), digest)
        self.assertTrue(self.values['audiooutput.passthrough'])

    def test_active_playback_refuses_without_checkpoint(self):
        self.active = [{'type': 'video', 'playerid': 1}]
        with self.assertRaisesRegex(RuntimeError, 'Playback active'):
            self.run_mode('deploy')
        self.assertFalse(self.module.CHECKPOINT.exists())

    def test_original_drift_refuses(self):
        (self.module.LIVE / 'select.wav').write_bytes(b'drift')
        with self.assertRaisesRegex(RuntimeError, 'Original sound drift'):
            self.run_mode('deploy')
        self.assertFalse(self.module.CHECKPOINT.exists())

    def test_reload_failure_restores_original_files_and_theme(self):
        self.fail_next_reload = True
        with self.assertRaisesRegex(RuntimeError, 'Could not reload'):
            self.run_mode('deploy')
        m = self.module
        self.assertTrue(all(m.sha(m.LIVE / n) == d for n, d in m.EXPECTED.items()))
        self.assertEqual(self.values['lookandfeel.soundskin'], 'resource.uisounds.asterhome')

    def test_rollback_refuses_newer_sound_drift(self):
        self.run_mode('deploy')
        (self.module.LIVE / 'select.wav').write_bytes(b'newer')
        with self.assertRaisesRegex(RuntimeError, 'Installed sound drift'):
            self.run_mode('rollback')


if __name__ == '__main__':
    unittest.main()
