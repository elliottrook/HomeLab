import importlib.util,json,shutil,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import build_books_sync as builder
spec=importlib.util.spec_from_file_location('books_deploy',Path(__file__).parent/'tools/deploy_books_sync.py')
deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)

class DeployTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.storage=Path(tmp.name).resolve()
        snapshot=self.storage/'snapshot';snapshot.mkdir()
        source=Path(__file__).parent.parent
        for name,location in (('service.py','plugin.audio.asterbooks/service.py'),('default.py','plugin.audio.asterbooks/default.py'),('MyMusicNav.xml','skin.asterhome/1080i/MyMusicNav.xml')):
            (snapshot/name).write_bytes((source/location).read_bytes())
        p=patch.object(builder,'BEFORE',{name:builder.sha((snapshot/name).read_bytes()) for name in builder.BEFORE});p.start();self.addCleanup(p.stop)
        stage=self.storage/'.aster-staging/aster-books-sync1';self.expected=builder.build(snapshot,stage)
        self.manifest=json.loads((stage/'manifest.json').read_text())
        for row in self.manifest['files']:
            if row['before_sha256'] is not None:
                path=self.storage/row['path'];path.parent.mkdir(parents=True,exist_ok=True)
                name='MyMusicNav.xml' if row['path']==builder.SKIN else Path(row['path']).name
                path.write_bytes((snapshot/name).read_bytes())
        bridge=self.storage/(builder.PLUGIN+'resources/lib/bridge.py');bridge.parent.mkdir(parents=True,exist_ok=True)
        bridge.write_bytes((source/'plugin.audio.asterbooks/resources/lib/bridge.py').read_bytes())
        self.proof='postcheck-'+str(time.time_ns())+'.json';directory=self.storage/'.aster-checkpoints/aster-music-progressive-20261024';directory.mkdir(parents=True)
        (directory/self.proof).write_text(json.dumps(dict(approved_search_details_files_verified=6,av_language_settings_verified=68,
            **{k:True for k in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off')})))
        p=patch.object(deploy.subprocess,'run',return_value=SimpleNamespace(stdout='0'));self.process=p.start();self.addCleanup(p.stop)
    def run_install(self):return deploy.run('install',self.expected,self.proof,self.storage)
    def test_build_exact_9_files_and_ui_keeps_controls(self):
        self.assertEqual(len(self.manifest['files']),9)
        self.assertEqual({r['path'] for r in self.manifest['files']},deploy.TARGETS)
        data=(self.storage/'.aster-staging/aster-books-sync1/payload'/builder.SKIN).read_text()
        self.assertIn('AsterBooks.SyncStatus',data);self.assertIn('PlayerControl(Stop)',data)
        self.assertIn('id="9104"',data)
    def test_install_verify_and_rollback_preserves_server_state_and_new_libraries(self):
        self.assertEqual(self.run_install()['files_verified'],9)
        self.assertTrue(deploy.run('verify',self.expected,'unused',self.storage)['verified'])
        result=deploy.run('rollback',self.expected,'unused',self.storage)
        self.assertTrue(result['server_progress_untouched']);self.assertFalse((self.storage/builder.FLAG).exists())
        for row in self.manifest['files']:
            if row['before_sha256'] is not None:self.assertEqual(deploy.sha(self.storage/row['path']),row['before_sha256'])
        self.assertTrue((self.storage/(builder.PLUGIN+'resources/lib/books_sync.py')).exists())
    def test_newer_edits_refuse_rollback(self):
        self.run_install();(self.storage/(builder.PLUGIN+'service.py')).write_text('newer')
        with self.assertRaisesRegex(RuntimeError,'installed-drift'):deploy.run('rollback',self.expected,'unused',self.storage)
    def test_successor_and_exact_predecessor_restore(self):
        self.run_install()
        first=self.storage/'.aster-staging/aster-books-sync1';second=self.storage/'.aster-staging/aster-books-sync2'
        with patch.object(builder,'FIRST_SHA',self.expected),patch.object(deploy,'FIRST_SHA',self.expected):
            digest=builder.successor(first,second)
            self.assertTrue(deploy.run('install',digest,self.proof,self.storage)['installed'])
            self.assertTrue(deploy.run('rollback',digest,'unused',self.storage)['rolled_back'])
        self.assertTrue(deploy.run('verify',self.expected,'unused',self.storage)['verified'])
    def test_unknown_predecessor_or_stale_proof_refuses_before_restart(self):
        target=self.storage/(builder.PLUGIN+'service.py');old=target.read_bytes();target.write_text('newer')
        with self.assertRaisesRegex(RuntimeError,'predecessor'):self.run_install()
        target.write_bytes(old)
        with patch.object(deploy.time,'time',return_value=time.time()+200):
            with self.assertRaisesRegex(RuntimeError,'fresh'):self.run_install()
        self.process.assert_not_called()
    def test_activation_failure_restores_three_originals_and_retires_flag(self):
        original=deploy.atomic
        def fail(path,data):
            if path.name=='active-manifest.json':raise OSError('synthetic-activation-failure')
            original(path,data)
        with patch.object(deploy,'atomic',side_effect=fail):
            with self.assertRaises(OSError):self.run_install()
        for row in self.manifest['files']:
            if row['before_sha256'] is not None:self.assertEqual(deploy.sha(self.storage/row['path']),row['before_sha256'])
        self.assertFalse((self.storage/builder.FLAG).exists())
        self.assertTrue((self.storage/'.aster-checkpoints/aster-books-sync-20261025/aster-books-sync1/retired-progress-enabled.json').exists())
    def test_sleep_successor_exact_thirteen_files_and_reverse_restore(self):
        self.run_install();first=self.storage/'.aster-staging/aster-books-sync1'
        fifth=self.storage/'.aster-staging/aster-books-sync5';shutil.copytree(first,fifth)
        manifest=dict(self.manifest,stage='aster-books-sync5',previous_manifest_sha256=builder.FOURTH_SHA)
        raw=(json.dumps(manifest,indent=2)+'\n').encode();(fifth/'manifest.json').write_bytes(raw)
        digest=builder.sha(raw);active=self.storage/'.aster-checkpoints/aster-books-sync-20261025/active-manifest.json';active.write_bytes(raw)
        sixth=self.storage/'.aster-staging/aster-books-sync6'
        with patch.object(builder,'FIFTH_SHA',digest),patch.object(deploy,'FIFTH_SHA',digest):
            candidate=builder.successor(fifth,sixth)
            rows=json.loads((sixth/'manifest.json').read_text())['files']
            self.assertEqual({r['path'] for r in rows},deploy.TARGETS|deploy.SLEEP_TARGETS)
            self.assertEqual(deploy.run('install',candidate,self.proof,self.storage)['files_verified'],13)
            self.assertTrue(deploy.run('rollback',candidate,'unused',self.storage)['rolled_back'])
        self.assertEqual(active.read_bytes(),raw)
        for row in manifest['files']:self.assertEqual(deploy.sha(self.storage/row['path']),row['sha256'])
