"""No network is used. Popen/socket calls are mocks; delay tests use fake clocks."""
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
import s0_live_candidate as live
import s0_lxc100_observe as observe
from s0_probe_timing import inspect_worker
from s0_probe_journal import Journal
from s0_dns_observe import collect_stub_dns
from test_s0_lxc100_candidate import props,cgroup,canary
from test_s0_probe_lifecycle import DNS


class TimingTests(unittest.TestCase):
    def test_delayed_collectors_share_aggregate_budget(self):
        now=[0.0];seen=[]
        answers={'unit-properties':props(),'cgroup':cgroup(),'canary-stat':canary()}
        def call(op,deadline):
            seen.append((op,deadline));now[0]+=2
            return answers[op]
        result=inspect_worker(call,0,clock=lambda:now[0])
        self.assertEqual(result[0]['main_pid'],123)
        self.assertEqual([x[1] for x in seen],[8,6,4])
        self.assertLess(now[0],8)

    def test_late_ready_and_delayed_response_fail_without_further_queries(self):
        for start_delay,delays,expected_calls in [(8,[0],0),(7,[1],1),(0,[3,5],2),(0,[3,3,2],3)]:
            with self.subTest(start_delay=start_delay,delays=delays):
                now=[start_delay];calls=[];steps=iter(delays)
                answers={'unit-properties':props(),'cgroup':cgroup(),'canary-stat':canary()}
                def call(op,deadline):
                    calls.append(op);self.assertGreater(deadline,0)
                    now[0]+=next(steps);return answers[op]
                with self.assertRaises(TimeoutError):inspect_worker(call,0,clock=lambda:now[0])
                self.assertEqual(len(calls),expected_calls)


class LiveCandidateTests(unittest.TestCase):
    def test_real_bundle_pin_and_tamper_rejection(self):
        raw=live.MANIFEST.read_bytes();pin=hashlib.sha256(raw).hexdigest()
        value=live.verify_bundle(pin);self.assertEqual(value['command_catalog_sha256'],observe.catalog_digest())
        with self.assertRaises(ValueError):live.verify_bundle('0'*64)
        changed=json.loads(raw);changed['artifacts']['/etc/shadow']='0'*64
        raw=json.dumps(changed).encode()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'manifest';p.write_bytes(raw)
            with patch.object(live,'MANIFEST',p),self.assertRaises(ValueError):live.verify_bundle(hashlib.sha256(raw).hexdigest())

    def test_exact_spawn_only_and_no_generic_options(self):
        with patch.object(live,'verify_bundle',return_value={'command_catalog_sha256':observe.catalog_digest()}),patch.object(subprocess,'Popen') as popen:
            adapter=live.FixedAdapter('review-pin')
            args={'env':{'LANG':'C','LC_ALL':'C'},'stdin':subprocess.DEVNULL,'stdout':subprocess.PIPE,'stderr':subprocess.PIPE,'start_new_session':True,'close_fds':True}
            expected=observe.command_catalog()['health'];adapter.spawn(expected,**args)
            popen.assert_called_once_with(expected,**args)
            for bad in (['/bin/sh','-c','anything'],observe.command_catalog()['stop-only-probe'],observe.command_catalog()['remove-canary']):
                with self.assertRaises(ValueError):adapter.spawn(bad,**args)
            with self.assertRaises(ValueError):adapter.spawn(expected,**dict(args,shell=True))
            self.assertEqual(popen.call_count,1)

    def test_guarded_cleanup_spawn_receipt_validation(self):
        from s0_owned_cleanup import argv
        from test_s0_probe_lifecycle import CleanupTests
        args={'env':{'LANG':'C','LC_ALL':'C'},'stdin':subprocess.DEVNULL,'stdout':subprocess.PIPE,'stderr':subprocess.PIPE,'start_new_session':True,'close_fds':True}
        with patch.object(live,'verify_bundle',return_value={}),patch.object(subprocess,'Popen') as popen:
            adapter=live.FixedAdapter('pin');expected=argv(CleanupTests().receipt())
            adapter.spawn(expected,**args);popen.assert_called_once_with(expected,**args)
            bad=expected.copy();bad[-1]+=' injected'
            with self.assertRaises(ValueError):adapter.spawn(bad,**args)

    def test_dns_fixed_target_and_packet(self):
        sock=Mock();sock.recvfrom.side_effect=DNS().recvfrom
        with patch.object(live.socket,'socket',return_value=sock) as factory:
            result=collect_stub_dns(socket_factory=live.FixedDNS)
            self.assertEqual(len(result['responses']),2)
            self.assertEqual(factory.call_count,2)
            sock.connect.assert_called_with(('192.168.20.20',53))
            self.assertEqual(sock.close.call_count,2)
            client=live.FixedDNS()
            with self.assertRaises(ValueError):client.sendto(b'bad',('8.8.8.8',53))
            with self.assertRaises(ValueError):client.recvfrom(8192)
            client.close()

    def test_prepared_path_exclusive_journal_with_stub_adapter_only(self):
        adapter=Mock();adapter.bundle={'command_catalog_sha256':observe.catalog_digest()}
        def fixture_run(journal,root_hash,**kwargs):
            self.assertEqual(kwargs['reviewed_manifest_sha256'],'review-pin')
            journal.append('begin',{'manifest_sha256':'review-pin'})
            return {'status':'stub-only'}
        with tempfile.TemporaryDirectory() as tmp,patch.object(live,'JOURNAL',Path(tmp)/'attempt'),patch.object(live,'FixedAdapter',return_value=adapter),patch.object(live,'run_candidate',side_effect=fixture_run):
            self.assertEqual(live._prepared_one_shot('review-pin'),{'status':'stub-only'})
            with self.assertRaises(FileExistsError):live._prepared_one_shot('review-pin')
            with Journal(Path(tmp)/'attempt') as journal:self.assertEqual(journal.records[0]['data']['manifest_sha256'],'review-pin')
        adapter.spawn.assert_not_called();adapter.dns.assert_not_called()

    def test_public_invocation_unconditionally_disabled(self):
        with patch.object(live,'_prepared_one_shot') as prepared:
            with self.assertRaises(PermissionError):live.invoke_once(approved=True,reviewed_pin='x')
            prepared.assert_not_called()


if __name__=='__main__':unittest.main()
