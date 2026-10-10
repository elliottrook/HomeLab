"""State machine tests with invented response bytes only; no remote commands."""
import copy
import json
import socket
import struct
import subprocess
import unittest
from unittest.mock import patch

import s0_probe_state as p


def responses():
    service={'running':True,'health':'healthy','restarts':0}
    health={'host':'running','pihole':service,'containers':{'pihole':service,'fixture-app':{'running':True,'health':'none','restarts':0}},
            'guest_mem_available':1024*1024**2,'cgroup_memory_current':128*1024**2,
            'cgroup_memory_max':1024*1024**2,'memory_psi_some_avg10':0}
    packet=(struct.pack('!6H',p.QUERY_ID,0x8180,1,0,0,0)+p.QUESTION).hex()
    dns={'responses':[{'packet_hex':packet,'elapsed_ms':10},{'packet_hex':packet,'elapsed_ms':11}]}
    values={
        'preflight-unit':{'load_state':'not-found','raw_stdout':'LoadState=not-found\n','stderr_empty':True,'exit_code':0},
        'preflight-paths':{'canary_directory_absent':True,'runtime_probe_absent':True},
        'preflight-health':health,'preflight-dns':dns,
        'create':{'created_exclusively':True,'directory_mode':0o755,'file_mode':0o644},
        'run-start':{'started_by_attempt':True,'unit':'aster-s0-feasibility-20260926.service','invocation_id':'fixture-invocation-owned'},
        'inspect-running':{'properties':p.EXPECTED,'phase':'ready','checks':dict.fromkeys(p.CHECKS,True),'invocation_id':'fixture-invocation-owned'},
        'run-result':{'phase':'done','passed':True,'exit_code':0,'invocation_id':'fixture-invocation-owned'},
        'postflight-health':health,'postflight-dns':dns,'final-health':health,'final-dns':dns,
        'stop':{'stopped_owned_unit':True,'invocation_id':'fixture-invocation-owned'},
        'inspect-cleanup':{'directory_owned_by_attempt':True,'exact_directory_mode':True,'exact_file_mode':True,
                           'exact_canary_content':True,'no_extra_entries':True,'unit_absent':True,'cgroup_absent':True},
        'remove-canary':{'removed_only_owned_canary_and_directory':True},
        'verify-cleanup':{'unit_absent':True,'cgroup_absent':True,'directory_absent':True,'runtime_probe_absent':True}}
    result={k:p.envelope(v) for k,v in values.items()}
    result['preflight-unit']={'returncode':0,'stdout':b'LoadState=not-found\n','stderr':b''}
    return result


def change(data,op,fn):
    value=json.loads(data[op]['stdout']);fn(value);data[op]=p.envelope(value)


class ProbeStateTests(unittest.TestCase):
    def runfake(self,data=None):return p.run_dry(p.FakeTransport(responses() if data is None else data))

    def test_success_order_is_exact(self):
        result=self.runfake()
        self.assertEqual(result['status'],'fixture-pass')
        self.assertEqual(result['operation_order'],['preflight-unit','preflight-paths','preflight-health',
            'preflight-dns','create','run-start','inspect-running','run-result','postflight-health',
            'postflight-dns','stop','inspect-cleanup','remove-canary','verify-cleanup','final-health','final-dns'])
        self.assertTrue(result['cleanup_verified']);self.assertFalse(result['live_authorized'])

    def test_no_io_or_subprocess(self):
        with patch.object(socket,'socket',side_effect=AssertionError('network')), \
             patch.object(subprocess,'Popen',side_effect=AssertionError('process')), \
             patch('builtins.open',side_effect=AssertionError('file')):
            self.assertEqual(self.runfake()['status'],'fixture-pass')

    def test_real_transport_and_subclass_rejected(self):
        with self.assertRaises(PermissionError):p.real_transport(approved=True)
        class Other(p.FakeTransport):pass
        with self.assertRaises(PermissionError):p.run_dry(Other(responses()))
        with self.assertRaises(PermissionError):p.run_dry(lambda _:None)

    def test_failure_at_every_transition_never_passes(self):
        for op in responses():
            with self.subTest(op=op):
                data=responses();data[op]=None;result=self.runfake(data)
                self.assertNotEqual(result['status'],'fixture-pass')
                if op.startswith('preflight'):
                    self.assertNotIn('create',result['operation_order'])
                    self.assertNotIn('stop',result['operation_order'])
                    self.assertNotIn('remove-canary',result['operation_order'])
                else:self.assertIn('verify-cleanup',result['operation_order'])

    def test_stderr_exit_and_oversize_rejected(self):
        for value in ({'returncode':1,'stdout':b'{}','stderr':b''},
                      {'returncode':0,'stdout':b'{}','stderr':b'warning'},
                      {'returncode':0,'stdout':b'x'*8193,'stderr':b''},
                      {'returncode':False,'stdout':b'{}','stderr':b''}):
            data=responses();data['preflight-unit']=value
            self.assertFalse(self.runfake(data)['create_attempted'])

    def test_exact_loadstate_and_absence(self):
        for raw in (b'LoadState=loaded\n',b'LoadState=not-found',b'',b'LoadState=not-found\nwarning'):
            data=responses();data['preflight-unit']['stdout']=raw
            self.assertFalse(self.runfake(data)['create_attempted'])
        data=responses();change(data,'preflight-paths',lambda x:x.update(canary_directory_absent=False))
        self.assertFalse(self.runfake(data)['create_attempted'])

    def test_bad_dns_id_flags_question_or_latency(self):
        for mutation in ('id','rcode','query','latency'):
            data=responses()
            def edit(value):
                row=value['responses'][0];raw=bytearray.fromhex(row['packet_hex'])
                if mutation=='id':raw[0]^=1
                if mutation=='rcode':raw[3]|=3
                if mutation=='query':raw[13]^=1
                if mutation=='latency':row['elapsed_ms']=2001
                row['packet_hex']=raw.hex()
            change(data,'preflight-dns',edit)
            self.assertFalse(self.runfake(data)['create_attempted'])

    def test_health_headroom_and_psi(self):
        for key,val in [('host','degraded'),('guest_mem_available',1),('cgroup_memory_max',1),
                        ('memory_psi_some_avg10',1.1)]:
            data=responses();change(data,'preflight-health',lambda x:x.update({key:val}))
            self.assertFalse(self.runfake(data)['create_attempted'])

    def test_post_health_changed_stop_and_cleanup_still_attempted(self):
        data=responses()
        def edit(x):x['pihole']['restarts']=1;x['containers']['pihole']['restarts']=1
        change(data,'postflight-health',edit)
        result=self.runfake(data)
        self.assertFalse(result['postflight_health_unchanged'])
        self.assertIn('stop',result['operation_order']);self.assertIn('remove-canary',result['operation_order'])
        self.assertNotEqual(result['status'],'fixture-pass')

    def test_no_delete_when_creation_unknown(self):
        data=responses();data['create']=None;result=self.runfake(data)
        self.assertNotIn('run-start',result['operation_order'])
        self.assertNotIn('remove-canary',result['operation_order'])
        self.assertIn('inspect-cleanup',result['operation_order'])

    def test_no_unowned_unit_stop_after_unknown_start(self):
        data=responses();data['run-start']=None;result=self.runfake(data)
        self.assertNotIn('stop',result['operation_order'])
        self.assertIn('manual-unit-recovery-required',result['failure_stages'])
        self.assertNotEqual(result['status'],'fixture-pass')

    def test_isolation_property_denial_and_identity_changes(self):
        for field in p.EXPECTED:
            data=responses()
            change(data,'inspect-running',lambda x:x['properties'].update({field:None}))
            result=self.runfake(data)
            self.assertNotIn('run-result',result['operation_order'])
            self.assertIn('stop',result['operation_order'])
        data=responses();change(data,'inspect-running',lambda x:x.update(invocation_id='other'))
        self.assertNotEqual(self.runfake(data)['status'],'fixture-pass')

    def test_false_denial_and_failed_worker(self):
        for check in p.CHECKS:
            data=responses();change(data,'inspect-running',lambda x:x['checks'].update({check:False}))
            self.assertNotEqual(self.runfake(data)['status'],'fixture-pass')
        data=responses();change(data,'run-result',lambda x:x.update(exit_code=1))
        self.assertNotEqual(self.runfake(data)['status'],'fixture-pass')

    def test_cleanup_every_bad_guard_refuses_removal(self):
        for key in json.loads(responses()['inspect-cleanup']['stdout']):
            data=responses();change(data,'inspect-cleanup',lambda x:x.update({key:False}))
            result=self.runfake(data)
            self.assertNotIn('remove-canary',result['operation_order'])
            self.assertNotEqual(result['status'],'fixture-pass')

    def test_verify_cleanup_requires_all_absent(self):
        data=responses();change(data,'verify-cleanup',lambda x:x.update(runtime_probe_absent=False))
        self.assertFalse(self.runfake(data)['cleanup_verified'])

    def test_bounded_evidence_no_raw_values_or_warning_echo(self):
        data=responses();data['run-result']['stderr']=b'INVENTED-DO-NOT-ECHO'
        result=self.runfake(data);encoded=json.dumps(result).encode()
        self.assertLessEqual(len(encoded),8192)
        self.assertNotIn(b'INVENTED-DO-NOT-ECHO',encoded)
        self.assertNotIn(b'packet_hex',encoded)

    def test_unknown_operations_and_json_duplicates(self):
        with self.assertRaises(ValueError):p.FakeTransport({'arbitrary-command':{}})
        data=responses();data['preflight-unit']['stdout']=b'{"a":1,"a":2}'
        self.assertFalse(self.runfake(data)['create_attempted'])


if __name__=='__main__':unittest.main()
