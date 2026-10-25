import hashlib,importlib.util,json,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import xml.etree.ElementTree as ET
from build_global_search import build
from global_search import Hit,SearchUnavailable
from search_handoff import route_for
import movie_player
spec=importlib.util.spec_from_file_location('movie_deploy',Path(__file__).parent/'tools/deploy_movie_search.py')
deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)

class MovieBuildTests(unittest.TestCase):
    def test_native_page_and_opt_in_only_id_route(self):
        hit=Hit('movie',7,'Not a command,(x)','')
        with self.assertRaises(SearchUnavailable):route_for(hit)
        route=route_for(hit,movie=True)
        self.assertEqual(route.expected,'7');self.assertNotIn(hit.title,route.command)
        self.assertIn('/movie.py,7)',route.command)
        with self.assertRaises(SearchUnavailable):route_for(Hit('movie',True,'T',''),movie=True)
        with tempfile.TemporaryDirectory() as folder:
            stage=Path(folder)/'candidate';build(stage,True,True,movie_player.MOVIE_STAGE)
            manifest=json.loads((stage/'manifest.json').read_text())
            self.assertEqual(set(r['path'] for r in manifest['files']),movie_player.MEMBERS)
            self.assertEqual(len(manifest['files']),13);self.assertEqual(manifest['movie_page'],11130)
            native=ET.parse(stage/'overlay/custom_1130_movie.xml').getroot()
            self.assertEqual(native.findtext('previouswindow'),'1127')
            controls={c.get('id'):c for c in native.findall('.//control') if c.get('id')}
            self.assertEqual(set(controls),{'200','201','202','400'})
            for control in controls.values():
                for direction in ('onup','ondown','onleft','onright'):self.assertIn(control.findtext(direction),controls)
            self.assertNotIn("rpc('Player.Open'",(stage/'movie.py').read_text())
            self.assertNotIn('WindowXML',(stage/'movie.py').read_text())
            self.assertIn('movie_enabled',(stage/'default.py').read_text())
    def test_stage_active_native_members_and_playback_guards_are_pinned(self):
        with tempfile.TemporaryDirectory() as folder:
            storage=Path(folder);stage=storage/'.aster-staging'/movie_player.MOVIE_STAGE
            build(stage,True,True,movie_player.MOVIE_STAGE)
            active=storage/'.aster-checkpoints/aster-global-search-20261024/active-manifest.json'
            active.parent.mkdir(parents=True);active.write_bytes((stage/'manifest.json').read_bytes())
            for source,target in movie_player.TARGETS.items():
                path=storage/'.kodi/addons/skin.asterhome'/target;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((stage/source).read_bytes())
            guard=storage/'.kodi/addons/skin.asterhome/guard.py';guard.write_bytes(b'guard')
            with patch.object(movie_player,'GUARDS',{'skin.asterhome/guard.py':hashlib.sha256(b'guard').hexdigest()}):
                movie_player.verify_stage(storage)
                guard.write_bytes(b'drift')
                with self.assertRaises(movie_player.MovieUnavailable):movie_player.verify_stage(storage)
                guard.write_bytes(b'guard');active.write_bytes(b'foreign')
                with self.assertRaises(movie_player.MovieUnavailable):movie_player.verify_stage(storage)

class MovieDeployTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);base=Path(temporary.name)
        for key in ('ROOT','STAGING','SKIN','PROOFS'):
            path=base/key;path.mkdir();p=patch.object(deploy,key,path);p.start();self.addCleanup(p.stop)
        for obj,key,value in ((deploy.os,'uname',SimpleNamespace(nodename='AsterTV')),
                              (deploy.subprocess,'run',SimpleNamespace(stdout='0'))):
            p=patch.object(obj,key,return_value=value);mock=p.start();self.addCleanup(p.stop)
            if key=='run':self.run=mock
        previous=deploy.STAGING/'aster-global-search-ui9';build(previous,True,True,previous.name)
        self.previous=deploy.digest(previous/'manifest.json')
        p=patch.object(deploy,'PREVIOUS_SEARCH',self.previous);p.start();self.addCleanup(p.stop)
        candidate=deploy.STAGING/deploy.MOVIE_STAGE;build(candidate,True,True,candidate.name)
        manifest=json.loads((candidate/'manifest.json').read_text());manifest['previous_manifest_sha256']=self.previous
        (candidate/'manifest.json').write_text(json.dumps(manifest));self.sha=deploy.digest(candidate/'manifest.json')
        (deploy.ROOT/'active-manifest.json').write_bytes((previous/'manifest.json').read_bytes())
        for source,target in deploy.TARGETS.items():
            if target==deploy.NEW:continue
            path=deploy.SKIN/target;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((previous/source).read_bytes())
        self.proof='postcheck-'+str(time.time_ns())+'.json'
        (deploy.PROOFS/self.proof).write_text(json.dumps(dict(approved_search_details_files_verified=5,av_language_settings_verified=68,
            **{k:True for k in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off')})))
    def install(self):deploy.main(['install',self.sha,self.proof])
    def test_install_restore_and_retained_new_xml(self):
        self.install();self.assertTrue((deploy.SKIN/deploy.NEW).exists())
        self.assertEqual(len(list((deploy.ROOT/deploy.MOVIE_STAGE/'isolated-restore').rglob('*.xml'))),5)
        deploy.main(['rollback',self.sha,'unused'])
        self.assertFalse((deploy.SKIN/deploy.NEW).exists());self.assertEqual(deploy.digest(deploy.ROOT/'active-manifest.json'),self.previous)
        self.assertTrue((deploy.ROOT/deploy.MOVIE_STAGE/'retired-movie-window.xml').exists())
    def test_unknown_predecessor_new_target_and_fence_refused(self):
        for mode in ('original','new','fence'):
            if mode=='original':path=deploy.SKIN/'1080i/Home.xml'
            elif mode=='new':path=deploy.SKIN/deploy.NEW
            else:path=deploy.ROOT/'handoff-pending.json'
            old=path.read_bytes() if path.exists() else None;path.write_bytes(b'foreign')
            with self.assertRaises(RuntimeError):self.install()
            self.run.assert_not_called()
            if old is None:path.unlink()
            else:path.write_bytes(old)
    def test_activation_failure_restores_five_and_retains_new(self):
        atomic=deploy.atomic
        def fail(path,data):
            if path==deploy.ROOT/'active-manifest.json' and data!=path.read_bytes():raise OSError('simulated')
            atomic(path,data)
        with patch.object(deploy,'atomic',side_effect=fail):
            with self.assertRaises(OSError):self.install()
        self.assertEqual(deploy.digest(deploy.ROOT/'active-manifest.json'),self.previous)
        self.assertFalse((deploy.SKIN/deploy.NEW).exists())
        self.assertTrue((deploy.ROOT/deploy.MOVIE_STAGE/'failed-movie-window.xml').exists())
        for source,target in deploy.TARGETS.items():
            if target!=deploy.NEW:self.assertEqual((deploy.SKIN/target).read_bytes(),(deploy.STAGING/'aster-global-search-ui9'/source).read_bytes())
    def test_rollback_refuses_drift_before_modification(self):
        self.install();(deploy.SKIN/deploy.NEW).write_text('foreign')
        with self.assertRaisesRegex(RuntimeError,'installed-drift'):deploy.main(['rollback',self.sha,'unused'])
        self.assertEqual(deploy.digest(deploy.ROOT/'active-manifest.json'),self.sha)
    def test_recovery_tools_are_paired_with_the_exact_staged_contract(self):
        self.install();before=self.run.call_count;deploy.main(['preserve-tools',self.sha,'unused'])
        directory=deploy.ROOT/deploy.MOVIE_STAGE/'recovery-tools'
        manifest=json.loads((directory/'manifest.json').read_text())
        self.assertEqual(manifest['stage_manifest_sha256'],self.sha)
        self.assertEqual({r['path'] for r in manifest['files']},{'deploy_movie_search.py','movie_player.py'})
        for row in manifest['files']:self.assertEqual(deploy.digest(directory/row['path']),row['sha256'])
        self.assertEqual((directory/'movie_player.py').read_bytes(),(deploy.STAGING/deploy.MOVIE_STAGE/'resources/lib/movie_player.py').read_bytes())
        self.assertEqual(self.run.call_count,before)

if __name__=='__main__':unittest.main()
