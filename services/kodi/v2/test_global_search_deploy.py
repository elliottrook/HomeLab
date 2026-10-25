import hashlib,importlib.util,json,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from build_global_search import build

spec=importlib.util.spec_from_file_location('search_deploy',Path(__file__).parent/'tools/deploy_global_search_preview.py')
deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)

class SearchDeployTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.paths={key:root/key for key in ('ROOT','SKIN','STAGING','PROOFS')}
        for key,path in self.paths.items():
            path.mkdir();p=patch.object(deploy,key,path);p.start();self.addCleanup(p.stop)
        p=patch.object(deploy.os,'uname',return_value=SimpleNamespace(nodename='AsterTV'));p.start();self.addCleanup(p.stop)
        p=patch.object(deploy.subprocess,'run',return_value=SimpleNamespace(stdout='0'));self.run=p.start();self.addCleanup(p.stop)
        self.name='aster-global-search-ui1';self.stage=deploy.STAGING/self.name;self.sha=build(self.stage)
        self.proof='postcheck-'+str(time.time_ns())+'.json'
        data=dict(candidate=64,approved_series_integration_files_verified=2,approved_video_scrub_files_verified=2,
                  **{key:True for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off')})
        (deploy.PROOFS/self.proof).write_text(json.dumps(data))
        adapter=hashlib.sha256((self.stage/'resources/lib/global_search.py').read_bytes()).hexdigest()
        (deploy.ROOT/'native-search-1.json').write_text(json.dumps(dict(passed=True,checks_enforced=True,home_preserved=True,source_sha256=adapter)))
        (deploy.SKIN/'Home.xml').write_text('<window id="0"/>')

    def prepare(self):deploy.main(['prepare',self.name,self.sha,self.proof])

    def test_prepare_restore_and_rollback(self):
        self.prepare()
        self.assertTrue((deploy.SKIN/deploy.NATIVE).is_file())
        self.assertEqual((deploy.ROOT/'prepared-manifest.json').read_bytes(),(self.stage/'manifest.json').read_bytes())
        deploy.main(['rollback',self.name,self.sha,'unused'])
        self.assertFalse((deploy.SKIN/deploy.NATIVE).exists())
        self.assertTrue((deploy.ROOT/self.name/'disabled-native-search.xml').is_file())
        self.assertEqual((deploy.SKIN/'Home.xml').read_text(),'<window id="0"/>')

    def test_drift_never_overwritten(self):
        (deploy.SKIN/deploy.NATIVE).write_text('unknown-user-file')
        with self.assertRaisesRegex(RuntimeError,'new-native-only'):self.prepare()
        self.assertEqual((deploy.SKIN/deploy.NATIVE).read_text(),'unknown-user-file')
        self.run.assert_not_called()

    def test_legacy_tool_cannot_dismantle_newer_details_integration(self):
        (deploy.ROOT/'active-manifest.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError,'newer-search-integration-active'):self.prepare()
        self.run.assert_not_called()

    def test_id_conflict_fails_before_stop(self):
        (deploy.SKIN/'other.xml').write_text('<window id="1127"/>')
        with self.assertRaisesRegex(RuntimeError,'native-id-conflict'):self.prepare()
        self.run.assert_not_called()

    def test_known_appledouble_only(self):
        (deploy.SKIN/'._Home.xml').write_bytes(b'\x00\x05\x16\x07resource-fork')
        self.prepare()

    def test_stage_and_missing_native_pass_fail_closed(self):
        (self.stage/'default.py').write_text('changed')
        with self.assertRaisesRegex(RuntimeError,'stage-member'):self.prepare()
        self.run.assert_not_called()

    def test_install_failure_quarantines_new_xml(self):
        atomic=deploy.atomic
        def fail(path,data):
            if path.name=='prepared-manifest.json':raise OSError('simulated')
            atomic(path,data)
        with patch.object(deploy,'atomic',side_effect=fail):
            with self.assertRaises(OSError):self.prepare()
        self.assertFalse((deploy.SKIN/deploy.NATIVE).exists())
        self.assertTrue((deploy.ROOT/self.name/'unactivated-native-search.xml').is_file())
        self.assertEqual(self.run.call_args[0][0],['systemctl','start','kodi'])

    def test_rollback_requires_stopped_and_exact_hash(self):
        self.prepare();self.run.return_value=SimpleNamespace(stdout='100')
        with self.assertRaisesRegex(RuntimeError,'stop-kodi-first'):deploy.main(['rollback',self.name,self.sha,'unused'])
        self.run.return_value=SimpleNamespace(stdout='0')
        (deploy.SKIN/deploy.NATIVE).write_text('other')
        with self.assertRaisesRegex(RuntimeError,'known-prepared-stage'):deploy.main(['rollback',self.name,self.sha,'unused'])
        self.assertEqual((deploy.SKIN/deploy.NATIVE).read_text(),'other')

if __name__=='__main__':unittest.main()
