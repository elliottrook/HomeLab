import importlib.util,json,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import build_movie_stop_guard as builder
from build_global_search import build as search_build
spec=importlib.util.spec_from_file_location('stop_deploy',Path(__file__).parent/'tools/deploy_movie_stop_guard.py')
deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)

class StopGuardTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.storage=Path(tmp.name)
        self.old=self.storage/'.aster-staging'/builder.OLD
        search_build(self.old,True,True,'aster-global-search-ui12')
        (self.old/'movie.py').write_text('# Synthetic predecessor controller\n')
        manifest=json.loads((self.old/'manifest.json').read_text());manifest['stage']=builder.OLD
        home=self.old/'overlay/Home.xml';home.write_bytes(home.read_bytes().replace(b'aster-global-search-ui12/',(builder.OLD+'/').encode()))
        for row in manifest['files']:
            data=(self.old/row['path']).read_bytes();row.update(sha256=builder.digest(data),bytes=len(data))
        (self.old/'manifest.json').write_text(json.dumps(manifest));self.before=deploy.sha(self.old/'manifest.json')
        for module in (builder,deploy):
            p=patch.object(module,'OLD_SHA',self.before);p.start();self.addCleanup(p.stop)
        self.new=self.storage/'.aster-staging'/builder.NEW;self.after=builder.build(self.old,self.new)
        self.root=self.storage/'.aster-checkpoints/aster-global-search-20261024';self.root.mkdir(parents=True)
        self.active=self.root/'active-manifest.json';self.active.write_bytes((self.old/'manifest.json').read_bytes())
        for row in manifest['files']:
            if row['path'].startswith('overlay/'):
                name=row['path'][8:];path=self.storage/'.kodi/addons/skin.asterhome'/('tools/' if name.endswith('.py') else '1080i/')/name
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((self.old/row['path']).read_bytes())
        self.home=self.storage/'.kodi/addons/skin.asterhome/1080i/Home.xml'
        self.proof='postcheck-'+str(time.time_ns())+'.json';proofdir=self.storage/'.aster-checkpoints/aster-music-progressive-20261024';proofdir.mkdir()
        (proofdir/self.proof).write_text(json.dumps(dict(approved_search_details_files_verified=6,av_language_settings_verified=68,
            **{k:True for k in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off')})))
        p=patch.object(deploy.subprocess,'run',return_value=SimpleNamespace(stdout='0'));self.process=p.start();self.addCleanup(p.stop)
    def install(self):return deploy.run('install',self.after,self.proof,self.storage)
    def test_exact_install_and_isolated_restore(self):
        before=self.home.read_bytes();self.assertEqual(self.install()['changed_targets'],2)
        self.assertEqual(deploy.sha(self.active),self.after)
        self.assertTrue(deploy.run('rollback',self.after,'unused',self.storage)['rolled_back'])
        self.assertEqual(self.home.read_bytes(),before);self.assertEqual(deploy.sha(self.active),self.before)
        self.assertTrue(self.new.exists())
    def test_only_three_payload_members_change(self):
        old=json.loads((self.old/'manifest.json').read_text());new=json.loads((self.new/'manifest.json').read_text())
        hashes={r['path']:r['sha256'] for r in old['files']}
        changed={r['path'] for r in new['files'] if r['sha256']!=hashes[r['path']]}
        self.assertEqual(changed,{'movie.py','resources/lib/movie_player.py','overlay/Home.xml'})
        with self.assertRaises(ValueError):builder.build(self.old,self.new)
    def test_drift_and_fence_refuse_before_restart(self):
        self.home.write_bytes(b'foreign')
        with self.assertRaisesRegex(RuntimeError,'predecessor'):self.install()
        self.process.assert_not_called()
        self.home.write_bytes((self.old/'overlay/Home.xml').read_bytes())
        (self.root/'handoff-pending.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError,'fence'):self.install()
        self.process.assert_not_called()
    def test_stale_proof_and_bad_payload_refused(self):
        with self.assertRaisesRegex(RuntimeError,'fresh'):self._stale()
        (self.new/'movie.py').write_text('drift')
        with self.assertRaisesRegex(RuntimeError,'member-drift'):self.install()
        self.process.assert_not_called()
    def _stale(self):
        with patch.object(deploy.time,'time',return_value=time.time()+200):self.install()
    def test_install_failure_restores_exact_predecessor(self):
        original=deploy.atomic
        def fail(path,data):
            if path==self.active and builder.digest(data)==self.after:raise OSError('synthetic-write-failure')
            original(path,data)
        with patch.object(deploy,'atomic',side_effect=fail):
            with self.assertRaises(OSError):self.install()
        self.assertEqual(deploy.sha(self.active),self.before)
        self.assertEqual(self.home.read_bytes(),(self.old/'overlay/Home.xml').read_bytes())
    def test_rollback_refuses_newer_edits(self):
        self.install();self.home.write_bytes(b'newer')
        with self.assertRaisesRegex(RuntimeError,'installed-drift'):deploy.run('rollback',self.after,'unused',self.storage)
        self.assertEqual(self.home.read_bytes(),b'newer')
