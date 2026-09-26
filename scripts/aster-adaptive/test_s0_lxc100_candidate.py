"""Fixed observation/session tests using local stubs only, never LXC100."""
import ast
import contextlib
import io
import json
import os
import shlex
import socket
import struct
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import s0_lxc100_observe as o
import s0_fixed_session as session
import s0_dns_observe as dns_observe
import s0_probe_state as state
import s0_feasibility_supervisor as supervisor


def property_values():
    result={k:'' for k in o.PROPERTIES}
    result.update(LoadState='loaded',ActiveState='active',SubState='running',MainPID='123',
        InvocationID='a'*32,ControlGroup='/system.slice/'+o.UNIT,DynamicUser='yes',
        NoNewPrivileges='yes',PrivateNetwork='yes',ProtectSystem='strict',
        InaccessiblePaths='/etc /opt /srv /var /run',
        SystemCallFilter='~@network-io @mount clone clone3 fork vfork',
        MemoryMax='67108864',MemorySwapMax='0',TasksMax='1',RuntimeMaxUSec='15s',
        KillMode='control-group',ExecMainCode='0',ExecMainStatus='0',Result='success',
        Environment='LANG=C LC_ALL=C',
        UnsetEnvironment=next(x.split('=',1)[1] for x in supervisor.PROPERTIES if x.startswith('UnsetEnvironment=')))
    return result


def props(values=None):
    return {'returncode':0,'stdout':''.join(k+'='+v+'\n' for k,v in (values or property_values()).items()).encode(),'stderr':b''}


def cgroup():return state.envelope({'control_group':'/system.slice/'+o.UNIT,
                                   'memory_max':67108864,'memory_swap_max':0,'pids_max':1})


def canary():return state.envelope({'directory_dev':1,'directory_inode':2,'file_dev':1,'file_inode':3,'directory_mode':0o755,'file_mode':0o644})


def ready():return {'scope':'invented-fixture-only','phase':'ready','checks':dict.fromkeys(state.CHECKS,True),'pid':123}


class CollectorTests(unittest.TestCase):
    def test_fixed_catalog_and_pins(self):
        catalog=o.command_catalog();o.require_pinned_catalog(o.catalog_digest())
        for argv in catalog.values():
            self.assertEqual(argv[:len(supervisor.SSH)],list(supervisor.SSH))
            self.assertEqual(shlex.split(argv[-1])[:4],['pct','exec','100','--'])
        with self.assertRaises(ValueError):o.require_pinned_catalog('0'*64)
        with self.assertRaises(PermissionError):o.live_entry(approved=True)

    def test_all_source_strings_parse(self):
        for source in (o.HEALTH_SOURCE,o.PATH_SOURCE,o.CANARY_SOURCE,o.CGROUP_SOURCE,o.ABSENCE_SOURCE):ast.parse(source)

    def test_running_and_cgroup_normalization(self):
        result=o.parse_running(props(),cgroup());self.assertEqual(result['main_pid'],123)
        self.assertEqual(result['properties'],state.EXPECTED)
        for key,value in [('PrivateNetwork','no'),('MainPID','0'),('MemoryMax','max'),
                          ('RuntimeMaxUSec','30s'),('Environment','LANG=wrong LC_ALL=C'),
                          ('ControlGroup','/other'),('SystemCallFilter','@system-service')]:
            values=property_values();values[key]=value
            with self.assertRaises(ValueError):o.parse_running(props(values),cgroup())

    def test_duplicate_unknown_or_missing_properties(self):
        for raw in (props()['stdout']+b'MainPID=123\n',props()['stdout']+b'Unexpected=1\n',b'MainPID=123\n'):
            with self.assertRaises(ValueError):o.parse_properties({'returncode':0,'stdout':raw,'stderr':b''})

    def test_kernel_limits(self):
        bad=state.envelope({'control_group':'/system.slice/'+o.UNIT,'memory_max':67108864,'memory_swap_max':0,'pids_max':True})
        with self.assertRaises(ValueError):o.parse_running(props(),bad)

    def test_ownership_binding_and_pid_race(self):
        created={'returncode':0,'stdout':b'','stderr':b''}
        receipt=o.bind_ownership(created,canary(),ready(),props(),cgroup())
        self.assertEqual(receipt['invocation_id'],'a'*32)
        wrong=ready();wrong['pid']=456
        with self.assertRaises(ValueError):o.bind_ownership(created,canary(),wrong,props(),cgroup())
        created['returncode']=1
        with self.assertRaises(ValueError):o.bind_ownership(created,canary(),ready(),props(),cgroup())

    def test_canary_identity_cleanup(self):
        receipt={'canary':o.parse_canary(canary()),'invocation_id':'a'*32}
        values=property_values();values.update(ActiveState='inactive',MainPID='0')
        absent=state.envelope({'directory_absent':False,'runtime_probe_absent':True,'cgroup_absent':True})
        self.assertTrue(o.cleanup_allowed(receipt,canary(),props(values),absent))
        changed=json.loads(canary()['stdout']);changed['file_inode']=999
        self.assertFalse(o.cleanup_allowed(receipt,state.envelope(changed),props(values),absent))
        values['InvocationID']='b'*32
        self.assertFalse(o.cleanup_allowed(receipt,canary(),props(values),absent))

    def test_health_source_with_fixed_local_stubs(self):
        names=['homarr','authentik-homarr-ingress','authentik-code-ingress','code-server','beszel','homepage','beszel-agent','pihole','portainer']
        def fake_run(argv,**kwargs):
            self.assertNotIn('shell',kwargs)
            if argv[:3]==['/usr/bin/docker','ps','-a']:out=('\n'.join(names)+'\n').encode()
            elif argv[:2]==['/usr/bin/docker','inspect']:
                self.assertIn(argv[-1],names);out=b'true healthy 0\n'
            elif argv==['/usr/bin/systemctl','is-system-running']:out=b'running\n'
            else:raise AssertionError('unexpected command')
            return out
        readings={'/proc/meminfo':'MemAvailable: 1048576 kB\n','/sys/fs/cgroup/memory.current':'1',
                  '/sys/fs/cgroup/memory.max':str(1024**3),'/sys/fs/cgroup/memory.pressure':'some avg10=0.00 avg60=0.00\n'}
        output=io.StringIO()
        with patch.object(Path,'read_text',lambda p:readings[str(p)]),contextlib.redirect_stdout(output):
            exec(compile(o.HEALTH_SOURCE[len(o.BOUNDED_SOURCE):],'<fixed-health-fixture>','exec'),{'bounded':fake_run})
        self.assertEqual(o.parse_health({'returncode':0,'stdout':output.getvalue().encode(),'stderr':b''})['host'],'running')


    def test_collector_helper_bounds_local_children(self):
        for source,expected in [('print("ok")',None),
                                ('import os;os.write(1,b"x"*5000)',ValueError),
                                ('import time;time.sleep(30)',TimeoutError),
                                ('import sys;sys.stderr.write("warning")',ValueError)]:
            namespace={};exec(o.BOUNDED_SOURCE,namespace)
            namespace['_end']=__import__('time').monotonic()+.2
            argv=[sys.executable,'-I','-S','-B','-c',source]
            if expected:
                with self.assertRaises(expected):namespace['bounded'](argv)
            else:self.assertEqual(namespace['bounded'](argv),b'ok\n')


class SessionTests(unittest.TestCase):
    def spawn_fixture(self,source):
        def spawn(argv,**kwargs):
            self.assertIn(argv,o.command_catalog().values())
            self.assertEqual(kwargs['env'],{'LANG':'C','LC_ALL':'C'})
            return subprocess.Popen([sys.executable,'-I','-S','-B','-c',source],**kwargs)
        return spawn

    def test_default_denial_and_invalid_operation(self):
        with self.assertRaises(PermissionError):session.FixedSession('load-state',o.catalog_digest())
        with self.assertRaises(ValueError):session.FixedSession('arbitrary',o.catalog_digest())
        with self.assertRaises(PermissionError):session.live_entry(approved=True)

    def test_stream_ready_then_finish(self):
        source='import json,time; print(json.dumps({"phase":"ready"}),flush=True); time.sleep(.1); print(json.dumps({"phase":"done"}),flush=True)'
        s=session.FixedSession('run-proposal-only',o.catalog_digest(),spawn=self.spawn_fixture(source))
        try:
            self.assertEqual(s.await_ready(),{'phase':'ready'})
            result=s.finish();self.assertEqual(result['status'],'complete')
            self.assertTrue(result['remote_cleanup_required']);self.assertFalse(result['remote_cleanup_executed'])
        finally:s.close()

    def test_timeout_and_combined_limit(self):
        for source,expected in [('import time;time.sleep(30)','timeout'),
                ('import os,time;os.write(1,b"a"*5000);os.write(2,b"b"*5000);time.sleep(30)','output-limit')]:
            s=session.FixedSession('health',o.catalog_digest(),spawn=self.spawn_fixture(source),deadline=.2)
            result=s.finish();self.assertEqual(result['status'],expected)
            self.assertLessEqual(len(result['stdout'])+len(result['stderr']),8192)
            self.assertIsNotNone(s.process.returncode)

    def test_malformed_readiness(self):
        s=session.FixedSession('run-proposal-only',o.catalog_digest(),spawn=self.spawn_fixture('print("not-json",flush=True)'))
        try:
            with self.assertRaises(ValueError):s.await_ready()
        finally:s.close()


class DNSStubTests(unittest.TestCase):
    def test_default_denial(self):
        with self.assertRaises(PermissionError):dns_observe.collect_stub_dns()

    def test_fixed_query_response(self):
        test=self
        class SocketStub:
            def settimeout(self,t):test.assertEqual(t,2)
            def sendto(self,q,peer):
                test.assertEqual(peer,('192.168.20.20',53));test.assertEqual(q[12:],state.QUESTION)
            def recvfrom(self,n):
                test.assertEqual(n,513)
                return struct.pack('!6H',state.QUERY_ID,0x8180,1,0,0,0)+state.QUESTION,('192.168.20.20',53)
            def close(self):pass
        values=iter([0,.01,1,1.02])
        result=dns_observe.collect_stub_dns(socket_factory=SocketStub,clock=lambda:next(values))
        self.assertTrue(state.dns(result))


if __name__=='__main__':unittest.main()
