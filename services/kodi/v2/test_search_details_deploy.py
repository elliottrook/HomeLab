import hashlib,importlib.util,json,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from build_global_search import build
from build_series_integration import dispatcher as series_dispatcher

spec=importlib.util.spec_from_file_location('details_deploy',Path(__file__).parent/'tools/deploy_search_details.py')
deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)

class SearchDetailsDeployTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);base=Path(temp.name)
        for name in ('ROOT','STAGING','SKIN','PROOFS'):
            path=base/name;path.mkdir();p=patch.object(deploy,name,path);p.start();self.addCleanup(p.stop)
        for name,value in (('uname',SimpleNamespace(nodename='AsterTV')),):
            p=patch.object(deploy.os,name,return_value=value);p.start();self.addCleanup(p.stop)
        p=patch.object(deploy.subprocess,'run',return_value=SimpleNamespace(stdout='0'));self.run=p.start();self.addCleanup(p.stop)
        self.stage=deploy.STAGING/'aster-global-search-ui3';build(self.stage,details=True)
        native=(self.stage/'overlay/custom_1127_search.xml').read_bytes()
        prior=deploy.STAGING/'aster-global-search-ui2';prior.mkdir()
        raw=json.dumps(dict(files=[dict(path='overlay/custom_1127_search.xml',sha256=hashlib.sha256(native).hexdigest())])).encode()
        (prior/'manifest.json').write_bytes(raw);previous=hashlib.sha256(raw).hexdigest()
        (deploy.ROOT/'prepared-manifest.json').write_bytes(raw)
        p=patch.object(deploy,'PREVIOUS',previous);p.start();self.addCleanup(p.stop)
        path=self.stage/'manifest.json';manifest=json.loads(path.read_text());manifest['previous_manifest_sha256']=previous
        path.write_text(json.dumps(manifest));self.sha=deploy.digest(path)
        (deploy.SKIN/'1080i').mkdir();(deploy.SKIN/'tools').mkdir()
        (deploy.SKIN/'1080i/custom_1127_search.xml').write_bytes(native)
        original=(Path(__file__).parent.parent/'skin.asterhome/tools/select_dispatch.py').read_text()
        (deploy.SKIN/'tools/select_dispatch.py').write_text(series_dispatcher(original))
        detail=next(r['sha256'] for r in manifest['files'] if r['path']=='resources/lib/search_details.py')
        (deploy.ROOT/'native-details-1.json').write_text(json.dumps(dict(passed=True,checks_enforced=True,source_sha256=detail)))
        self.proof='postcheck-'+str(time.time_ns())+'.json'
        proof=dict(approved_series_integration_files_verified=2,approved_video_scrub_files_verified=2,
                   **{k:True for k in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off')})
        (deploy.PROOFS/self.proof).write_text(json.dumps(proof))
    def install(self):deploy.main(['install',self.sha,self.proof])
    def test_install_and_exact_rollback(self):
        self.install();deploy.main(['rollback',self.sha,'unused'])
        self.assertEqual(deploy.digest(deploy.SKIN/'tools/select_dispatch.py'),deploy.BEFORE)
        self.assertFalse((deploy.SKIN/'1080i/custom_1128_searchdetails.xml').exists())
        self.assertTrue((deploy.ROOT/'aster-global-search-ui3/disabled-details.xml').exists())
    def test_unknown_dispatcher_never_replaced(self):
        (deploy.SKIN/'tools/select_dispatch.py').write_text('unknown')
        with self.assertRaisesRegex(RuntimeError,'predecessor-drift'):self.install()
        self.run.assert_not_called()
    def test_conflicting_native_id_fails_before_stop(self):
        (deploy.SKIN/'1080i/other.xml').write_text('<window id="1128"/>')
        with self.assertRaisesRegex(RuntimeError,'details-id-conflict'):self.install()
        self.run.assert_not_called()
    def test_activation_failure_restores_predecessors(self):
        atomic=deploy.atomic
        def fail(path,data):
            if path.name=='active-manifest.json':raise OSError('simulated')
            atomic(path,data)
        with patch.object(deploy,'atomic',side_effect=fail):
            with self.assertRaises(OSError):self.install()
        self.assertEqual(deploy.digest(deploy.SKIN/'tools/select_dispatch.py'),deploy.BEFORE)
        self.assertFalse((deploy.SKIN/'1080i/custom_1128_searchdetails.xml').exists())
        self.assertEqual(self.run.call_args[0][0],['systemctl','start','kodi'])
    def test_running_or_drifted_rollback_is_refused(self):
        self.install();self.run.return_value=SimpleNamespace(stdout='100')
        with self.assertRaisesRegex(RuntimeError,'stop-kodi-first'):deploy.main(['rollback',self.sha,'unused'])
        self.run.return_value=SimpleNamespace(stdout='0')
        (deploy.SKIN/'tools/select_dispatch.py').write_text('unknown')
        with self.assertRaisesRegex(RuntimeError,'installed-drift'):deploy.main(['rollback',self.sha,'unused'])

if __name__=='__main__':unittest.main()
