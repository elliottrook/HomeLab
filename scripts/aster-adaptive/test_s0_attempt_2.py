"""Attempt-2 dynamic inventory/host resource tests; invented data only."""
import copy
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import s0_lxc_memory as memory
import s0_lxc100_observe as observe
import s0_live_candidate as live
from s0_probe_state import envelope
from test_s0_probe_lifecycle import health_response


def host(**changes):
    values={'status':'running','maxmem':'4294967296','mem':'739872768','maxswap':'536870912','swap':'0','type':'lxc','vmid':'100'}
    values.update(changes)
    return {'returncode':0,'stdout':''.join(k+': '+v+'\n' for k,v in values.items()).encode(),'stderr':b''}


class AttemptTwoTests(unittest.TestCase):
    def test_fixed_host_accounting_and_bounds(self):
        result=memory.parse_host(host());self.assertEqual(result['maxmem'],4294967296)
        for changes in ({'maxmem':'max'},{'mem':'-1'},{'mem':'4294967296'},{'swap':'1'},
                        {'maxswap':'-1'},{'status':'stopped'},{'secret':'unrecognized'}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):memory.parse_host(host(**changes))
        for raw in (host()['stdout']+b'mem: 1\n',b'status: running\n',b'x'*4097):
            with self.assertRaises(ValueError):memory.parse_host({'returncode':0,'stdout':raw,'stderr':b''})

    def test_full_captured_pct_output(self):
        path=Path(__file__).resolve().parents[2]/'docs/projects/AI Projects/experiments/s0-routing-descriptive-v1/fixtures/pct-status-100-run001-diagnosis.txt'
        actual=memory.parse_host({'returncode':0,'stdout':path.read_bytes(),'stderr':b''})
        self.assertEqual(actual,{'status':'running','maxmem':4294967296,'mem':739872768,'maxswap':536870912,'swap':0})
        raw=path.read_bytes()+b'new_unknown_field: 0\n'
        with self.assertRaises(ValueError):memory.parse_host({'returncode':0,'stdout':raw,'stderr':b''})

    def test_known_pressure_and_text_fields_are_strict(self):
        extras={'name':'docker','type':'lxc','tags':'community-script;docker',
                **{field:'0' for field in memory.PRESSURE_FIELDS}}
        self.assertEqual(memory.parse_host(host(**extras))['maxmem'],4294967296)
        for field in memory.PRESSURE_FIELDS:
            for value in ('-1','NaN','inf','1e999','1'*65,''):
                with self.subTest(field=field,value=value),self.assertRaises(ValueError):memory.parse_host(host(**{field:value}))
        for field,value in [('vmid','101'),('vmid','100.0'),('cpus','0'),('pid','1.5'),('uptime','-1'),('type','qemu'),('type',''),('name','bad name'),('name','x'*129),
                            ('tags','a;;b'),('tags','a;a'),('tags','x'*65),('tags','a;bad tag'),
                            ('tags',';'.join('tag'+str(i) for i in range(17))),('unknownpressure','0')]:
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):memory.parse_host(host(**{field:value}))

    def test_guest_max_ignored_host_limit_used(self):
        baseline,resources=memory.combined_health(health_response(),host())
        self.assertEqual(baseline['host_maxmem'],4294967296)
        self.assertEqual(resources['host_memory_current'],739872768)
        self.assertNotIn("root/'memory.max'",observe.HEALTH_SOURCE)
        self.assertIn("root/'memory.max'",observe.CGROUP_SOURCE)
        with self.assertRaises(ValueError):memory.combined_health(health_response(),host(maxmem='2147483648'))

    def test_dynamic_stopped_inventory_and_exact_comparison(self):
        value=json.loads(health_response()['stdout'])
        stopped={'running':False,'state':'exited','health':'none','restarts':0}
        value['containers']['code-server-pre-authentik']=stopped
        before,_=memory.combined_health(envelope(value),host())
        self.assertFalse(before['containers']['code-server-pre-authentik']['running'])
        for change in ('add','remove','restart','state','limits'):
            after=copy.deepcopy(value);resources=host()
            if change=='add':after['containers']['new-service']=stopped
            if change=='remove':del after['containers']['code-server-pre-authentik']
            if change=='restart':after['containers']['code-server-pre-authentik']['restarts']=1
            if change=='state':after['containers']['code-server-pre-authentik'].update(running=True,state='running')
            if change=='limits':resources=host(maxswap='1073741824')
            observed,_=memory.combined_health(envelope(after),resources)
            self.assertNotEqual(observed,before)

    def test_inventory_and_guest_pressure_rejection(self):
        base=json.loads(health_response()['stdout'])
        for kind in ('name','count','unhealthy','restarting','pressure','headroom'):
            value=copy.deepcopy(base)
            if kind=='name':value['containers']['bad;name']=value['pihole']
            if kind=='count':value['containers'].update({f'fixture{i}':value['pihole'] for i in range(32)})
            if kind=='unhealthy':value['pihole']['health']='unhealthy'
            if kind=='restarting':value['pihole']['state']='restarting'
            if kind=='pressure':value['memory_psi_some_avg10']=1
            if kind=='headroom':value['guest_mem_available']=512
            with self.subTest(kind=kind),self.assertRaises(ValueError):memory.guest_health(value)

    def test_dynamic_collector_uses_no_guest_root_limit(self):
        names=['pihole','code-server-pre-authentik']
        calls=[]
        def bounded(argv):
            calls.append(argv)
            if argv[:3]==['/usr/bin/docker','ps','-a']:return '\n'.join(names).encode()
            if argv[:2]==['/usr/bin/docker','inspect']:
                return b'true running healthy 0\n' if argv[-1]=='pihole' else b'false exited none 0\n'
            if argv==['/usr/bin/systemctl','is-system-running']:return b'running\n'
            raise AssertionError('unexpected command')
        readings={'/proc/meminfo':'MemTotal: 4194304 kB\nMemAvailable: 3504251 kB\n','/sys/fs/cgroup/memory.pressure':'some avg10=0.00 avg60=0.00\n'}
        output=io.StringIO()
        with patch.object(Path,'read_text',lambda p:readings[str(p)]),contextlib.redirect_stdout(output):
            exec(observe.HEALTH_SOURCE[len(observe.BOUNDED_SOURCE):],{'bounded':bounded})
        baseline,_=memory.combined_health({'returncode':0,'stdout':output.getvalue().encode(),'stderr':b''},host())
        self.assertEqual(set(baseline['containers']),set(names));self.assertEqual(len(calls),4)

    def test_distinct_attempt_identity_and_fresh_approval(self):
        self.assertIn('attempt-2',live.JOURNAL.name)
        self.assertIn('attempt-2',live.APPROVAL.name)
        self.assertIn('attempt-2',live.MANIFEST.name)
        value=json.loads(live.APPROVAL.read_text())
        self.assertEqual(value['scope']['attempt'],'run-002')
        self.assertEqual(value['release']['human_approval'],'approved-for-run-002')
        self.assertEqual(value['release']['one_shot_execution'],'consumed-run-002-failed-preflight')
        self.assertEqual(value['provenance'],live.PROVENANCE)
        self.assertEqual(observe.command_catalog()['host-lxc-status'][-1],'pct status 100 --verbose')


if __name__=='__main__':unittest.main()
