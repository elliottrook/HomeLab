"""Integrated lifecycle uses invented local child output and socket stubs only."""
import copy
import json
import os
import shlex
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import s0_probe_lifecycle as life
import s0_lxc100_observe as observe
import s0_owned_cleanup as cleanup
from s0_probe_journal import Journal
import s0_probe_state as state
from test_s0_lxc100_candidate import props,cgroup,canary,ready


class DNS:
    def settimeout(self,t):pass
    def sendto(self,*a):pass
    def recvfrom(self,n):return struct.pack('!6H',state.QUERY_ID,0x8180,1,0,0,0)+state.QUESTION,('192.168.20.20',53)
    def close(self):pass


def health_response():
    status={'running':True,'state':'running','health':'healthy','restarts':0}
    return state.envelope({'host':'running','pihole':status,'containers':{'pihole':status},
                           'guest_mem_total':4*1024**3,'guest_mem_available':1024**3,'memory_psi_some_avg10':0})


class Transport:
    def __init__(self,fail=None):self.calls=[];self.fail=fail;self.children=[]
    def __call__(self,argv,**kw):
        catalog=observe.command_catalog()
        op=next((k for k,v in catalog.items() if v==argv),None)
        if op is None:
            inner=shlex.split(argv[-1]);assert inner[9]==cleanup.SOURCE
            op='guarded-cleanup'
            assert argv==cleanup.argv(json.loads(inner[10]))
        self.calls.append(op)
        outputs={'load-state':b'LoadState=not-found\n','paths':state.envelope({'canary_directory_absent':True,'runtime_probe_absent':True})['stdout'],
                 'health':health_response()['stdout'],'host-lxc-status':b'status: running\nmaxmem: 4294967296\nmem: 739872768\nmaxswap: 536870912\nswap: 0\ntype: lxc\nvmid: 100\n','create-owned-canary':canary()['stdout'],
                 'canary-stat':canary()['stdout'],'unit-properties':props()['stdout'],'cgroup':cgroup()['stdout'],
                 'guarded-cleanup':b'{"removed_owned_canary":true}',
                 'absence':state.envelope({'directory_absent':True,'runtime_probe_absent':True,'cgroup_absent':True})['stdout']}
        if op==self.fail:source='raise SystemExit(3)'
        elif op=='run-proposal-only':source='import time;print('+repr(json.dumps(ready()))+',flush=True);time.sleep(.5);print(\'{"scope":"invented-fixture-only","phase":"done","passed":true}\',flush=True)'
        else:source='import os;os.write(1,'+repr(outputs[op])+')'
        child=subprocess.Popen([sys.executable,'-I','-S','-B','-c',source],**kw);self.children.append(child);return child


class LifecycleTests(unittest.TestCase):
    def test_complete_sequence_and_durable_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            transport=Transport()
            with Journal(Path(tmp)/'attempt',create=True) as journal:
                result=life.run_candidate(journal,observe.catalog_digest(),spawn=transport,socket_factory=DNS)
                self.assertEqual(result['status'],'fixture-pass',journal.records)
                self.assertEqual(journal.recovery()['status'],'complete')
            with Journal(Path(tmp)/'attempt') as recovered:
                self.assertEqual(recovered.recovery()['status'],'complete')
                with self.assertRaises(ValueError):life.run_candidate(recovered,observe.catalog_digest(),spawn=transport,socket_factory=DNS)
            self.assertNotIn('stop-only-probe',transport.calls)
            self.assertTrue(all(p.poll() is not None for p in transport.children))

    def test_failure_at_each_operation_never_blind_cleanup(self):
        for failure in ['load-state','paths','health','host-lxc-status','create-owned-canary','run-proposal-only','unit-properties','cgroup','canary-stat','guarded-cleanup','absence']:
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as tmp:
                transport=Transport(failure)
                with Journal(Path(tmp)/'attempt',create=True) as journal:
                    result=life.run_candidate(journal,observe.catalog_digest(),spawn=transport,socket_factory=DNS)
                    self.assertEqual(result['status'],'failed-or-inconclusive')
                    self.assertFalse(journal.recovery()['automatic_delete_allowed'])
                self.assertNotIn('stop-only-probe',transport.calls)
                if failure not in ('guarded-cleanup','absence'):self.assertNotIn('guarded-cleanup',transport.calls)
                self.assertTrue(all(p.poll() is not None for p in transport.children))

    def test_interruptions_preserve_receipts_without_replay(self):
        for event in ('create-intent','canary-created','run-intent','ownership-bound','worker-completed','cleanup-intent'):
            with self.subTest(event=event),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'attempt';transport=Transport()
                with Journal(p,create=True) as journal:
                    append=journal.append
                    def interrupted(name,data):
                        append(name,data)
                        if name==event:raise KeyboardInterrupt()
                    journal.append=interrupted
                    with self.assertRaises(KeyboardInterrupt):
                        life.run_candidate(journal,observe.catalog_digest(),spawn=transport,socket_factory=DNS)
                with Journal(p) as recovered:
                    state=recovered.recovery()
                    self.assertFalse(state['automatic_stop_allowed'])
                    self.assertFalse(state['automatic_delete_allowed'])
                self.assertNotIn('guarded-cleanup',transport.calls)
                self.assertTrue(all(p.poll() is not None for p in transport.children))

    def test_default_transports_denied(self):
        with tempfile.TemporaryDirectory() as tmp,Journal(Path(tmp)/'attempt',create=True) as journal:
            self.assertEqual(life.run_candidate(journal,observe.catalog_digest())['status'],'failed-or-inconclusive')
            self.assertEqual(journal.records[-1]['data']['failure_boundary'],'command-load-state')
            self.assertEqual(journal.records[-1]['data']['failure_class'],'permission')
        with self.assertRaises(PermissionError):life.live_entry(approved=True)

    def test_bounded_failure_codes_distinguish_dns_and_journal_without_text(self):
        class TimeoutDNS(DNS):
            def recvfrom(self,n):raise TimeoutError('DO-NOT-RETAIN')
        with tempfile.TemporaryDirectory() as tmp,Journal(Path(tmp)/'dns',create=True) as journal:
            result=life.run_candidate(journal,observe.catalog_digest(),spawn=Transport(),socket_factory=TimeoutDNS)
            self.assertEqual(result['status'],'failed-or-inconclusive')
            self.assertEqual(journal.records[-1]['data'],{'stage':'preflight','mutation_attempted':False,
                'manual_recovery_required':False,'failure_boundary':'preflight-dns','failure_class':'timeout'})
            self.assertNotIn('DO-NOT-RETAIN',json.dumps(journal.records))
        with tempfile.TemporaryDirectory() as tmp,Journal(Path(tmp)/'journal',create=True) as journal:
            append=journal.append;failed=[False]
            def fail_once(event,data):
                if event=='preflight-verified' and not failed[0]:
                    failed[0]=True;raise OSError('DO-NOT-RETAIN')
                return append(event,data)
            journal.append=fail_once
            result=life.run_candidate(journal,observe.catalog_digest(),spawn=Transport(),socket_factory=DNS)
            self.assertEqual(result['status'],'failed-or-inconclusive')
            self.assertEqual(journal.records[-1]['data']['failure_boundary'],'preflight-journal')
            self.assertEqual(journal.records[-1]['data']['failure_class'],'io')
            self.assertNotIn('DO-NOT-RETAIN',json.dumps(journal.records))

    def test_failure_class_allowlist(self):
        cases=[(TimeoutError(),'timeout'),(PermissionError(),'permission'),(OSError(),'io'),
               (ValueError(),'validation'),(AssertionError(),'validation'),(RuntimeError(),'internal')]
        for error,expected in cases:
            with self.subTest(error=type(error).__name__):self.assertEqual(life.failure_class(error),expected)


class JournalTests(unittest.TestCase):
    def test_exclusive_and_interrupted_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'attempt'
            with Journal(p,create=True) as j:
                j.append('create-intent',{})
                with self.assertRaises(BlockingIOError):Journal(p)
            with Journal(p) as j:
                self.assertEqual(j.recovery()['last_event'],'create-intent')
                self.assertFalse(j.recovery()['automatic_rerun_allowed'])
            with self.assertRaises(FileExistsError):Journal(p,create=True)

    def test_corruption_gap_symlink_and_bound(self):
        for bad in ('truncated','gap','symlink'):
            with self.subTest(bad=bad),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'attempt'
                with Journal(p,create=True) as j:j.append('begin',{})
                file=p/'000.json'
                if bad=='truncated':file.write_bytes(b'{')
                elif bad=='gap':file.rename(p/'001.json')
                else:file.unlink();file.symlink_to('/dev/null')
                with self.assertRaises((ValueError,OSError)):Journal(p)
        with tempfile.TemporaryDirectory() as tmp,Journal(Path(tmp)/'attempt',create=True) as j:
            with self.assertRaises(ValueError):j.append('oversize',{'x':'a'*8192})


class CleanupTests(unittest.TestCase):
    def receipt(self):return {'canary':observe.parse_canary(canary()),'invocation_id':'a'*32,'main_pid':123,'completed':True}
    def test_typed_data_only(self):
        self.assertIn(cleanup.SOURCE,shlex.split(cleanup.argv(self.receipt())[-1]))
        for key,value in [('completed',False),('main_pid',True),('invocation_id','$(bad)')]:
            r=self.receipt();r[key]=value
            with self.assertRaises(ValueError):cleanup.argv(r)

    def test_guarded_cleanup_loaded_unloaded_and_mismatch(self):
        for mode in ('loaded','not-found','wrong-invocation','wrong-inode','running','cgroup-present'):
            with self.subTest(mode=mode):
                receipt=self.receipt()
                fields={'LoadState':'loaded','ActiveState':'inactive','MainPID':'0','InvocationID':'a'*32}
                if mode=='not-found':fields.update(LoadState='not-found',InvocationID='')
                if mode=='wrong-invocation':fields['InvocationID']='b'*32
                if mode=='running':fields['MainPID']='123'
                raw=''.join(k+'='+v+'\n' for k,v in fields.items()).encode()
                directory=SimpleNamespace(st_dev=1,st_ino=999 if mode=='wrong-inode' else 2,st_uid=0,st_mode=0o40755)
                file=SimpleNamespace(st_dev=1,st_ino=3,st_uid=0,st_nlink=1,st_mode=0o100644)
                def fake_open(path,*a,**kw):return 11 if path=='canary' else 10
                with patch('sys.argv',['probe',json.dumps(receipt)]),patch('os.open',side_effect=fake_open),patch('os.close'),patch('os.fstat',side_effect=lambda fd:directory if fd==10 else file),patch('os.listdir',return_value=['canary']),patch('os.read',return_value=b'x'),patch('os.stat',return_value=file),patch('os.lstat',return_value=directory),patch('os.path.exists',return_value=mode=='cgroup-present'),patch('os.path.lexists',return_value=False),patch('os.unlink') as unlink,patch('os.rmdir') as rmdir,patch('builtins.print'):
                    run=lambda:exec(cleanup.SOURCE[len(observe.BOUNDED_SOURCE):],{'bounded':lambda argv:raw})
                    if mode in ('loaded','not-found'):
                        run();unlink.assert_called_once_with('canary',dir_fd=10);rmdir.assert_called_once()
                    else:
                        with self.assertRaises(AssertionError):run()
                        unlink.assert_not_called();rmdir.assert_not_called()


if __name__=='__main__':unittest.main()
