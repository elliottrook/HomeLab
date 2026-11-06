"""Offline tests of the additive registered route; no live imports or IO."""
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent/'model-trial-20261106-r3'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


class RegisteredBridge(unittest.TestCase):
    def setUp(self):
        self.b = module('fixed_registered_bridge_test', HERE/'b60_exclusive_card_bridge.py')
        self.row = dict(booking_id='b60-exclusive-20261106-day-r3', owner='b60-stream-a',
            workload=self.b.WORKLOAD, kind='exclusive-stack', state='reserved',
            start_epoch=1000, end_epoch=3700, restore_buffer_seconds=900)
        self.spec = types.SimpleNamespace(workload_id=self.b.WORKLOAD, owner='b60-stream-a',
            runner_kind=self.b.KIND, request_count=2, per_request_timeout_seconds=60,
            deadline_seconds=1200, minimum_booking_seconds=2700,
            recovery_reserve_seconds=900, retryable_session=False,
            maximum_attempts=1, result_max_bytes=8192)
    def test_fixed_registration_window_and_identity(self):
        self.b.validate_row(self.row, self.spec, 1000)
        for key, value in [('workload', None), ('kind', 'smoke'), ('state', 'scheduled'),
                           ('owner', 'other-owner'), ('end_epoch', 3701), ('booking_id', '../escape')]:
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                self.b.validate_row(dict(self.row, **{key:value}), self.spec, 1000)
        for now in (999,1121):
            with self.assertRaises(RuntimeError): self.b.validate_row(self.row,self.spec,now)
    def test_no_retry_or_budget_widening(self):
        for key, value in [('maximum_attempts', 2), ('retryable_session', True),
                           ('deadline_seconds', 1800), ('request_count', 3)]:
            spec = types.SimpleNamespace(**vars(self.spec));setattr(spec,key,value)
            with self.assertRaises(RuntimeError):self.b.validate_row(self.row,spec,1000)
    def test_bridge_never_imports_inner_controller_or_gpu(self):
        tree = ast.parse((HERE/'b60_exclusive_card_bridge.py').read_bytes())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):imported.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):imported.add(node.module)
        self.assertFalse(imported & {'model_trial','lab_hours_reservations','torch','fixed_command'})
    def test_card_rejects_source_or_base_drift_and_extra_code(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);package=root/'package';package.mkdir();base=root/'base';base.mkdir()
            (root/'model-trial-cards').mkdir()
            sources={name:hashlib.sha256(name.encode()).hexdigest() for name in self.b.FILES}
            for name in sources:(package/name).write_bytes(name.encode())
            (package/'manifest.json').write_bytes(self.b.canonical(sources))
            pins={f'base{i}.py':hashlib.sha256(str(i).encode()).hexdigest() for i in range(30)}
            for i in range(30):(base/f'base{i}.py').write_text(str(i))
            base_sha=hashlib.sha256(self.b.canonical(pins)).hexdigest()
            card=dict(schema='b60-fixed-model-trial.v1',booking_id=self.row['booking_id'],
                start_epoch=1000,end_epoch=3700,source_sha256=sources,candidate_sha256=self.b.MODEL_SHA,
                base_source_map_sha256=base_sha,mode='qwen36-35b-reasoning-compatibility-v1',backup_history_sha256='b'*64)
            raw=self.b.canonical(card);(root/'model-trial-cards'/(self.row['booking_id']+'.json')).write_bytes(raw)
            with patch.object(self.b,'protected',side_effect=lambda p,**kw:Path(p).read_bytes()), \
                 patch.object(self.b,'BASE_SHA',base_sha):
                self.assertEqual(self.b.validate_card(self.row,root=root,package=package,base=base),hashlib.sha256(raw).hexdigest())
                (package/'model_trial.py').write_text('drift')
                with self.assertRaises(RuntimeError):self.b.validate_card(self.row,root=root,package=package,base=base)
                (package/'model_trial.py').write_text('model_trial.py')
                (package/'extra.py').write_text('unknown code')
                with self.assertRaises(RuntimeError):self.b.validate_card(self.row,root=root,package=package,base=base)
                (package/'extra.py').unlink();(base/'base0.py').write_text('drift')
                with self.assertRaises(RuntimeError):self.b.validate_card(self.row,root=root,package=package,base=base)
    def test_dispatch_is_once_only_and_child_is_isolated(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def run(command, **kw):calls.append((command,kw));return types.SimpleNamespace(returncode=0)
            with patch.object(self.b,'ROOT',Path(d)), patch.object(self.b.os,'geteuid',return_value=0), \
                 patch.object(self.b.os,'uname',return_value=types.SimpleNamespace(nodename='proxmox')):
                # The private disposable directory belongs to this test UID;
                # only root-identity observations are injected, never production.
                original=Path.lstat
                def info(path):
                    s=original(path)
                    return types.SimpleNamespace(st_mode=s.st_mode,st_uid=0)
                with patch.object(Path,'lstat',info), \
                     patch.object(self.b,'validate_card',return_value='a'*64), \
                     patch.object(self.b,'require_incident_closed',return_value=None), \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(self.b.dispatch(self.row,self.spec,clock=lambda:1001,runner=run),0)
                    with self.assertRaises(FileExistsError):
                        self.b.dispatch(self.row,self.spec,clock=lambda:1002,runner=run)
                self.assertEqual(len(calls),1)
                command, kw=calls[0]
                self.assertEqual(command[:3],['/usr/bin/python3','-B',str(self.b.PACKAGE/'model_trial.py')])
                self.assertEqual(command[3:],['launch','--booking-id',self.row['booking_id']])
                self.assertEqual(kw['timeout'],25)
                intent=json.loads((Path(d)/'exclusive-dispatch'/(self.row['booking_id']+'.json')).read_bytes())
                self.assertEqual(intent['booking_identity']['workload'],self.b.WORKLOAD)
    def test_open_incident_blocks_and_missing_or_changed_evidence_cannot_clear_it(self):
        raw=self.b.canonical({'incident_id':self.b.INCIDENT,'state':'OPEN'})
        with patch.object(self.b,'protected',return_value=raw), \
             patch.object(self.b,'INCIDENT_SHA',hashlib.sha256(raw).hexdigest()):
            with self.assertRaisesRegex(RuntimeError,'DEVICE_INCIDENT_OPEN'):
                self.b.require_incident_closed()
        with patch.object(self.b,'protected',side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):self.b.require_incident_closed()
        with patch.object(self.b,'protected',return_value=b'closed'):
            with self.assertRaisesRegex(RuntimeError,'DEVICE_INCIDENT_EVIDENCE_DRIFT'):
                self.b.require_incident_closed()
    def test_failed_launch_is_burned_not_retried_or_claimed(self):
        # The immutable intent remains even if the outer launch fails; only a
        # new reviewed booking can dispatch again. No generic claim API exists.
        source=(HERE/'b60_exclusive_card_bridge.py').read_text()
        self.assertLess(source.index('os.O_CREAT|os.O_EXCL'),source.index('result = runner('))
        self.assertNotIn('.claim(',source)
        self.assertNotIn('host_exclusion(',source)
    def test_candidate_registry_preserves_all_other_workloads(self):
        build=module('capture_registration_builder_test',HERE/'build_registration.py')
        pins=build.build()
        candidate=module('capture_workloads_candidate_test',build.DEST/'lab_hours_workloads.py')
        old=module('capture_workloads_original_test',build.SOURCE/'lab_hours_workloads.py')
        self.assertEqual(set(candidate.WORKLOADS)-set(old.WORKLOADS),{self.b.WORKLOAD})
        self.assertIn(self.b.WORKLOAD,candidate.REGISTERED_WORKLOADS)
        self.assertEqual(set(candidate.REGISTERED_WORKLOADS),set(old.REGISTERED_WORKLOADS)|{self.b.WORKLOAD})
        for name,spec in old.WORKLOADS.items():
            self.assertEqual(vars(spec),vars(candidate.WORKLOADS[name]))
        candidate.validate_registry()
        result=candidate.validate_inactive_target(build.DEST,expected_uid=__import__('os').geteuid(),
              unit_root=build.DEST/'unused-units',workload_id=self.b.WORKLOAD)
        self.assertEqual(result['effects'],'not-attempted')
        self.assertEqual(len(candidate.workload(self.b.WORKLOAD).runtime_pins),1)
        old_manifest=json.loads((build.SOURCE/'release-snapshot.json').read_bytes())['manifest']
        new_manifest=json.loads((build.DEST/'lab_hours_release_manifest.json').read_bytes())
        for n,sha in old_manifest['pins'].items():
            if n not in pins:self.assertEqual(new_manifest['pins'][n],sha)
    def invoke_real_registered_branch(self, row, retry=False):
        build=module('capture_branch_builder_test',HERE/'build_registration.py');build.build()
        tree=ast.parse((build.DEST/'lab_hours_reserved_runner.py').read_bytes())
        run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        calls=[]
        class Store:
            def __init__(inner,*args):pass
            def get(inner,*args):calls.append('get');return row
            def claim(inner,*args,**kw):raise AssertionError('generic double claim')
        def dispatch(value,spec):
            calls.append('dispatch');self.b.validate_row(value,spec,1000);return 0
        ns={'os':types.SimpleNamespace(geteuid=lambda:0),'ReservationStore':Store,
            'RESERVATIONS':Path('/unused'),'PILOT':Path('/unused'),
            'load_manifest':lambda:calls.append('manifest'),
            'workload':lambda name:self.spec,'RunError':RuntimeError,'json':json}
        exec(compile(ast.Module(body=[run],type_ignores=[]),'actual_registered_branch','exec'),ns)
        mods={'lab_hours_workloads':types.SimpleNamespace(validate_registry=lambda:None,
            validate_inactive_target=lambda *a,**kw:None),
            'b60_exclusive_card_bridge':types.SimpleNamespace(dispatch=dispatch)}
        output=io.StringIO()
        with patch.dict(sys.modules,mods),contextlib.redirect_stdout(output):
            result=ns['run'](row['booking_id'],retry=retry)
        return result,calls,output.getvalue()
    def test_actual_global_branch_does_not_double_claim(self):
        result,calls,output=self.invoke_real_registered_branch(self.row)
        self.assertEqual(result,0)
        self.assertEqual(calls,['get','manifest','dispatch'])
    def test_actual_global_branch_refuses_retry_and_wrong_state(self):
        result,calls,output=self.invoke_real_registered_branch(self.row,retry=True)
        self.assertEqual(result,1);self.assertEqual(calls,['get'])
        result,calls,output=self.invoke_real_registered_branch(dict(self.row,state='scheduled'))
        self.assertEqual(result,1)
        self.assertFalse(json.loads(output)['qualification_claimed'])


if __name__=='__main__':unittest.main()
