"""No live connections: isolated canonical adoption and exact-file rollback."""
import importlib.util,shutil,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
from canonical_sound_compat import promote

class CanonicalDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        source=Path(__file__).parent/'tools/deploy_canonical_sounds.py'
        with patch.dict(sys.modules,{'xbmc':types.SimpleNamespace()}):
            spec=importlib.util.spec_from_file_location('canonical_trial',source)
            self.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.m)
        m=self.m;base=Path(self.temp.name);m.BASE=base/'stage';m.LIVE=base/'live';m.CHECKPOINT=base/'checkpoint'
        (m.BASE/'resources').mkdir(parents=True);m.LIVE.mkdir()
        (m.BASE/'masters').mkdir()
        resources=Path(__file__).parent.parent/'resource.uisounds.asterhome/resources'
        original={}
        config_source=source.with_name('deploy_canonical_clicks.py')
        spec=importlib.util.spec_from_file_location('canonical_clicks',config_source)
        config=importlib.util.module_from_spec(spec);spec.loader.exec_module(config)
        config.configure(m)
        m.BASE=base/'stage';m.LIVE=base/'live';m.CHECKPOINT=base/'checkpoint'
        for name in m.EXPECTED:
            shutil.copyfile(resources/name,m.BASE/'masters'/name)
            (m.BASE/'resources'/name).write_bytes(promote((resources/name).read_bytes()))
            (m.LIVE/name).write_bytes(('old-'+name).encode());original[name]=m.sha(m.LIVE/name)
        (m.LIVE/'sounds.xml').write_text('<sounds/>');m.ORIGINALS={h:dict(original) for h in ('AsterTV','AsterTVProd')}
        self.host='AsterTV';self.active=[];self.fail=False
        self.values={'lookandfeel.soundskin':'resource.uisounds.asterhome','audiooutput.passthrough':True}
        m.rpc=self.rpc
        p=patch.object(m.os,'uname',side_effect=lambda:types.SimpleNamespace(nodename=self.host));p.start();self.addCleanup(p.stop)
    def rpc(self,method,params=None):
        if method=='Settings.GetSettings':return {'settings':[dict(id=k,value=v) for k,v in self.values.items()]}
        if method=='Player.GetActivePlayers':return self.active
        if method=='Settings.SetSettingValue':
            if params['value'] and self.fail:self.fail=False;return False
            self.values[params['setting']]=params['value'];return True
        raise RuntimeError('unexpected-rpc')
    def test_hp_install_verify_and_exact_rollback(self):
        self.assertTrue(self.m.main('deploy')['timing_and_pcm_unchanged'])
        self.assertTrue(self.m.main('verify')['checkpoint_verified'])
        self.assertTrue(self.m.main('rollback')['rolled_back'])
        self.assertEqual(self.m.snapshot(),self.m.ORIGINALS[self.host])
    def test_production_install_does_not_change_settings(self):
        self.host='AsterTVProd';before=dict(self.values)
        self.assertEqual(self.m.main('deploy')['assets'],self.m.EXPECTED)
        self.assertEqual(self.values,before)
    def test_other_host_refused(self):
        self.host='other'
        with self.assertRaisesRegex(RuntimeError,'known-host'):self.m.main('deploy')
    def test_active_playback_refused_without_checkpoint(self):
        self.active=[dict(playerid=1,type='video')]
        with self.assertRaisesRegex(RuntimeError,'playback-active'):self.m.main('deploy')
        self.assertFalse(self.m.CHECKPOINT.exists())
    def test_master_and_predecessor_drift_refused(self):
        (self.m.BASE/'resources/select.wav').write_bytes(b'drift')
        with self.assertRaisesRegex(RuntimeError,'canonical-master-drift'):self.m.main('deploy')
        self.assertFalse(self.m.CHECKPOINT.exists())
    def test_reload_failure_restores_original_and_settings(self):
        self.fail=True;before=dict(self.values)
        with self.assertRaisesRegex(RuntimeError,'theme-reload-failed'):self.m.main('deploy')
        self.assertEqual(self.m.snapshot(),self.m.ORIGINALS[self.host]);self.assertEqual(self.values,before)
    def test_repeat_and_newer_asset_rollback_refused(self):
        self.m.main('deploy')
        with self.assertRaisesRegex(RuntimeError,'existing-checkpoint'):self.m.main('deploy')
        (self.m.LIVE/'select.wav').write_bytes(b'newer')
        with self.assertRaisesRegex(RuntimeError,'installed-drift'):self.m.main('rollback')
