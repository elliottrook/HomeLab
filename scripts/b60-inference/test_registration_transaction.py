"""Fault-inject the actual registry source transaction in disposable local files."""
import base64
import contextlib
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

SOURCE=Path(__file__).parent/'model-trial-20261106-r3/registration_install.py.txt'


class Transaction(unittest.TestCase):
    def fixture(self, root, failure=None):
        root=Path(root);pilot=root/'packages/full-inference-pilot';pilot.mkdir(parents=True)
        base=pilot.parent/'exclusive-session';base.mkdir()
        old={'lab_hours_workloads.py':b'old_registry = True\n',
             'lab_hours_reserved_runner.py':b'old_runner = True\n'}
        old_pins={n:hashlib.sha256(v).hexdigest() for n,v in old.items()}
        old['lab_hours_release_manifest.json']=json.dumps({'pins':old_pins}).encode()
        for n,v in old.items():(pilot/n).write_bytes(v)
        new={'lab_hours_workloads.py':b'new_registry = True\n',
             'lab_hours_reserved_runner.py':b'new_runner = True\n',
             'b60_exclusive_card_bridge.py':b'new_bridge = True\n'}
        new['lab_hours_release_manifest.json']=json.dumps({'pins':{n:hashlib.sha256(v).hexdigest() for n,v in new.items()}}).encode()
        b='b60-exclusive-20261106-day-r3'
        records=root/'reservations/records';records.mkdir(parents=True)
        row={'schema':'aster-lab-hours-reservation.v1','booking_id':b,'owner':'b60-stream-a',
             'workload':None,'kind':'exclusive-stack','state':'reserved','start_epoch':1000,
             'end_epoch':3700,'restore_buffer_seconds':900}
        canon=lambda v:json.dumps(v,sort_keys=True,separators=(',',':')).encode()
        (records/(b+'.json')).write_bytes(canon(row))
        class Bookings:
            @contextlib.contextmanager
            def locked(self):yield
            def _path(self,name):return records/(name+'.json')
            def _read_unlocked(self,path):return json.loads(path.read_bytes())
            def _write_unlocked(self,v):self._path(v['booking_id']).write_bytes(canon(v))
        def create(path,raw,mode=0o600):
            fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,mode)
            with os.fdopen(fd,'wb') as f:f.write(raw)
        def call(*args):
            if failure=='validation':raise RuntimeError('fake validator rejection')
            if failure=='concurrent':
                (pilot/'lab_hours_reserved_runner.py').write_text('unrelated concurrent source')
                raise RuntimeError('fake concurrent change')
            return json.dumps({'effects':'not-attempted'})
        ns={'BASE':base,'ROOT':root,'B':b,'os':os,'time':time,'hashlib':hashlib,'json':json,
            'base64':base64,'protected_bytes':lambda p,**kw:Path(p).read_bytes(),
            'canonical':canon,'create':create,'call':call,
            'REG_PREDECESSORS':{n:hashlib.sha256(v).hexdigest() for n,v in old.items()},
            'REG_FILES':{n:base64.b64encode(v).decode() for n,v in new.items()},
            'REG_SHA':{n:hashlib.sha256(v).hexdigest() for n,v in new.items()}}
        exec(compile(SOURCE.read_bytes(),str(SOURCE),'exec'),ns)
        return ns,Bookings(),row,pilot,old,new
    def test_success_changes_only_workload_and_preserves_old_sources(self):
        with tempfile.TemporaryDirectory() as d:
            ns,store,row,pilot,old,new=self.fixture(d)
            result=ns['install_registration'](store,row)
            bound=store._read_unlocked(store._path(row['booking_id']))
            self.assertEqual(bound,dict(row,workload='b60-qwen36-35b-failure-capture-v1'))
            self.assertTrue(result['owner_times_kind_state_preserved'])
            self.assertFalse(result['base30_modified'])
            for n,v in old.items():
                self.assertEqual((Path(d)/'registration-backups'/row['booking_id']/n).read_bytes(),v)
    def test_validation_failure_restores_exact_predecessors_without_binding(self):
        with tempfile.TemporaryDirectory() as d:
            ns,store,row,pilot,old,new=self.fixture(d,'validation')
            with self.assertRaises(RuntimeError):ns['install_registration'](store,row)
            self.assertEqual(store._read_unlocked(store._path(row['booking_id'])),row)
            for n,v in old.items():self.assertEqual((pilot/n).read_bytes(),v)
            self.assertFalse((pilot/'b60_exclusive_card_bridge.py').exists())
            self.assertTrue((Path(d)/'registration-backups'/row['booking_id']/'rollback.json').exists())
    def test_rollback_never_overwrites_foreign_source_or_claims_restore(self):
        with tempfile.TemporaryDirectory() as d:
            ns,store,row,pilot,old,new=self.fixture(d,'concurrent')
            with self.assertRaises(AssertionError):ns['install_registration'](store,row)
            self.assertEqual((pilot/'lab_hours_reserved_runner.py').read_text(),'unrelated concurrent source')
            self.assertFalse((Path(d)/'registration-backups'/row['booking_id']/'rollback.json').exists())
            self.assertEqual(store._read_unlocked(store._path(row['booking_id'])),row)


if __name__=='__main__':unittest.main()
