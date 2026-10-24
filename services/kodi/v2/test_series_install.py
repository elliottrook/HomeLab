import importlib.util,json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from build_series_preview import build as player_build
from build_series_integration import build,SOURCE,HERE

class SeriesInstallTests(unittest.TestCase):
    def setup_case(self,parent,passes=2):
        spec=importlib.util.spec_from_file_location('series_installer',HERE/'tools/install_series_integration.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        root=Path(parent);storage=root/'storage';stage=storage/'.aster-staging';stage.mkdir(parents=True)
        player_sha=player_build(stage/'aster-series-preview14')
        sha=build(stage/'aster-series-integration4','aster-series-preview14',player_sha)
        skin=storage/'.kodi/addons/skin.asterhome';(skin/'tools').mkdir(parents=True)
        (skin/'tools/select_dispatch.py').write_bytes(SOURCE.read_bytes())
        evidence=storage/'.aster-checkpoints/aster-music-progressive-20261024';evidence.mkdir(parents=True)
        proof='postcheck-'+str(time.time_ns())+'.json'
        (evidence/proof).write_text(json.dumps(dict(candidate=64,checks_enforced=True,no_player=True,
            original_empty_queue=True,all_lab_windows_closed=True,music_shuffle_off=True)))
        tests=storage/'.aster-checkpoints/aster-series-playback-20261024';tests.mkdir()
        for i in range(passes):(tests/f'native-player-{i}.json').write_text(json.dumps(dict(passed=True,checks_enforced=True,
            stage='aster-series-preview14',idle_empty=True)))
        module.ROOT=skin;module.CHECKPOINT=storage/'.aster-checkpoints/aster-series-integration-20261024'
        def mapped(value):
            path=Path(value)
            return root/str(path).lstrip('/') if str(path).startswith('/storage/') else path
        return module,skin,proof,sha,mapped

    def run_case(self,module,proof,sha,mapped):
        with patch.object(module.os,'uname',return_value=type('Host',(),dict(nodename='AsterTV'))()),patch.object(module,'Path',side_effect=mapped):
            module.main(['aster-series-integration4',sha,proof])

    def test_checkpoint_restore_activation_and_refusal_to_repeat(self):
        with tempfile.TemporaryDirectory() as parent:
            module,skin,proof,sha,mapped=self.setup_case(parent)
            self.run_case(module,proof,sha,mapped)
            self.assertEqual((module.CHECKPOINT/'isolated-restore/tools/select_dispatch.py').read_bytes(),SOURCE.read_bytes())
            manifest=json.loads((module.CHECKPOINT/'active-manifest.json').read_text())
            for row in manifest['files']:self.assertEqual(module.digest(skin/row['path']),row['sha256'])
            with self.assertRaises(RuntimeError):self.run_case(module,proof,sha,mapped)

    def test_one_native_pass_cannot_activate(self):
        with tempfile.TemporaryDirectory() as parent:
            module,skin,proof,sha,mapped=self.setup_case(parent,1)
            with self.assertRaisesRegex(RuntimeError,'two-native-player-passes-required'):self.run_case(module,proof,sha,mapped)
            self.assertEqual((skin/'tools/select_dispatch.py').read_bytes(),SOURCE.read_bytes())
            self.assertFalse((skin/'tools/aster_v2_series.py').exists())

    def test_source_drift_refuses_without_checkpoint_or_overwrite(self):
        with tempfile.TemporaryDirectory() as parent:
            module,skin,proof,sha,mapped=self.setup_case(parent)
            (skin/'tools/select_dispatch.py').write_text('owner change')
            with self.assertRaisesRegex(RuntimeError,'live-source-drift'):self.run_case(module,proof,sha,mapped)
            self.assertFalse(module.CHECKPOINT.exists())
            self.assertEqual((skin/'tools/select_dispatch.py').read_text(),'owner change')

    def test_failed_activation_restores_dispatcher_and_retains_new_helper(self):
        with tempfile.TemporaryDirectory() as parent:
            module,skin,proof,sha,mapped=self.setup_case(parent)
            atomic=module.atomic;failed=[]
            def fail_once(path,data,mode=0o644):
                if path==skin/'tools/select_dispatch.py' and data!=SOURCE.read_bytes() and not failed:
                    failed.append(True);raise OSError('synthetic-activation-failure')
                return atomic(path,data,mode)
            with patch.object(module,'atomic',side_effect=fail_once),self.assertRaises(OSError):self.run_case(module,proof,sha,mapped)
            self.assertEqual((skin/'tools/select_dispatch.py').read_bytes(),SOURCE.read_bytes())
            self.assertFalse((skin/'tools/aster_v2_series.py').exists())
            self.assertTrue((module.CHECKPOINT/'unactivated-helper.py').is_file())
            self.assertFalse((module.CHECKPOINT/'active-manifest.json').exists())

if __name__=='__main__':unittest.main()
