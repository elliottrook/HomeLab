import importlib.util
from datetime import datetime,timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

spec=importlib.util.spec_from_file_location('coordinator',Path(__file__).with_name('coordinator.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class Clock:
 def __init__(self,hour=21,minute=40):self.value=datetime(2026,10,12,hour,minute,tzinfo=ZoneInfo('America/Vancouver'))
 def now(self):return self.value
 def sleep(self,seconds):self.value+=timedelta(seconds=seconds)
class Transport:
 def __init__(self,clock,fail=None):self.clock=clock;self.fail=fail;self.calls=[]
 def __call__(self,host,*args,timeout=180):
  action=args[2] if host=='proxmox' else 'mirror';self.calls.append(action)
  if action==self.fail:raise RuntimeError('synthetic connection failure')
  if action=='prepare':return dict(host_time=self.clock.now().isoformat(),archive_name='vzdump-lxc-110-2026_10_12-02_39_23.tar.zst',sha256='a'*64,bytes=43*1024**3)
  if action=='mirror':return dict(archive_name='vzdump-lxc-110-2026_10_12-02_39_23.tar.zst',sha256='a'*64,bytes=43*1024**3,checked_at=self.clock.now().isoformat())
  if action=='drained':return {'drained':True}
  if action=='preflight':return {'collected_at':self.clock.now().isoformat()}
  if action=='status':return {'terminal':True,'success':True}
  return {'okay':True}
class Tests(unittest.TestCase):
 def test_stale_temporary_file_does_not_block_status(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'status.json';stale=Path(d)/'status.json.tmp'
   stale.write_text('interrupted prior write')
   s.atomic(path,{'stage':'ready'})
   self.assertEqual(json.loads(path.read_text()),{'stage':'ready'})
   self.assertEqual(stale.read_text(),'interrupted prior write')
   self.assertEqual(path.stat().st_mode & 0o777,0o600)
   self.assertEqual(list(Path(d).glob('.status.json.*.tmp')),[])
 def test_failed_replace_keeps_previous_state_and_cleans_only_own_temp(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'status.json';s.atomic(path,{'stage':'old'})
   unrelated=Path(d)/'status.json.tmp';unrelated.write_text('keep')
   with patch.object(s.os,'replace',side_effect=OSError('synthetic write failure')):
    with self.assertRaises(OSError):s.atomic(path,{'stage':'new'})
   self.assertEqual(json.loads(path.read_text()),{'stage':'old'})
   self.assertEqual(unrelated.read_text(),'keep')
   self.assertEqual(list(Path(d).glob('.status.json.*.tmp')),[])
 def test_nonfinite_status_rejected_before_file_creation(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):s.atomic(Path(d)/'status.json',{'time':float('nan')})
   self.assertEqual(list(Path(d).iterdir()),[])
 def run_case(self,root,clock,transport):return s.Coordinator(root,transport,clock.now,clock.sleep)
 def test_success_waits_for_windows_and_releases(self):
  with tempfile.TemporaryDirectory() as d:
   c=Clock();t=Transport(c);result=self.run_case(d,c,t).execute()
   self.assertTrue(result['completed']);self.assertEqual(t.calls,['prepare','mirror','reserve','drained','mirror','preflight','start','status','release'])
   self.assertEqual(c.now().hour,22);self.assertEqual(c.now().minute,15)
 def test_daytime_and_late_catchup_have_zero_remote_effects(self):
  for hour,minute in [(9,0),(21,39),(22,6),(23,59)]:
   with tempfile.TemporaryDirectory() as d:
    c=Clock(hour,minute);t=Transport(c);self.assertIn('skipped',self.run_case(d,c,t).execute());self.assertEqual(t.calls,[])
 def test_daily_duplicate_never_runs_again(self):
  with tempfile.TemporaryDirectory() as d:
   c=Clock();t=Transport(c);r=self.run_case(d,c,t);r.execute();before=list(t.calls)
   self.assertIn('skipped',r.execute());self.assertEqual(before,t.calls)
 def test_reservation_response_loss_still_attempts_release(self):
  with tempfile.TemporaryDirectory() as d:
   c=Clock();t=Transport(c,'reserve')
   with self.assertRaises(RuntimeError):self.run_case(d,c,t).execute()
   self.assertEqual(t.calls[-1],'release');self.assertNotIn('start',t.calls)
 def test_failed_preparation_does_not_reserve_gpu(self):
  with tempfile.TemporaryDirectory() as d:
   c=Clock();t=Transport(c,'prepare')
   with self.assertRaises(RuntimeError):self.run_case(d,c,t).execute()
   self.assertEqual(t.calls,['prepare'])
 def test_lost_coordinator_connection_leaves_recovery_unconfirmed(self):
  with tempfile.TemporaryDirectory() as d:
   c=Clock();t=Transport(c,'release')
   with self.assertRaises(RuntimeError):self.run_case(d,c,t).execute()
   events=json.loads((Path(d)/'status.json').read_text())['events']
   self.assertEqual(events[-1]['stage'],'recovery_unconfirmed');self.assertTrue(events[-1]['independent_host_watchdogs_retained'])
   records=list(Path(d).glob('*.result.json'))
   self.assertEqual(len(records),1)
   self.assertEqual(json.loads(records[0].read_text())['events'],events)
   self.assertTrue((Path(d)/'review-required.json').exists())
   self.assertEqual(t.calls.count('release'),1)
 def test_failed_experiment_and_failed_recovery_both_persist(self):
  with tempfile.TemporaryDirectory() as d:
   c=Clock();t=Transport(c)
   def transport(host,*args,**kwargs):
    if host=='proxmox' and args[2] in ('start','release'):
     t.calls.append(args[2]);raise RuntimeError('synthetic failure')
    return t(host,*args,**kwargs)
   with self.assertRaises(RuntimeError):self.run_case(d,c,transport).execute()
   record=json.loads(next(Path(d).glob('*.result.json')).read_text())
   stages=[event['stage'] for event in record['events']]
   self.assertIn('failed',stages);self.assertIn('recovery_unconfirmed',stages)
   self.assertNotIn('accepted_sycl_and_schedules_restored',stages)
   self.assertTrue((Path(d)/'review-required.json').exists())
 def test_failed_preparation_still_has_terminal_record(self):
  with tempfile.TemporaryDirectory() as d:
   c=Clock();t=Transport(c,'prepare')
   with self.assertRaises(RuntimeError):self.run_case(d,c,t).execute()
   record=json.loads(next(Path(d).glob('*.result.json')).read_text())
   self.assertEqual(record['events'][-1]['stage'],'failed')
   self.assertNotIn('release',t.calls)
 def test_transport_does_not_require_interactive_agent(self):
  with patch.object(s.subprocess,'run') as run:
   run.return_value.returncode=0;run.return_value.stdout='{}'
   s.call('proxmox','/bin/true')
   self.assertIn('IdentityAgent=none',run.call_args.args[0])
   self.assertIn('StrictHostKeyChecking=yes',run.call_args.args[0])
 def test_read_only_check_has_no_claim_wait_or_mutation(self):
  with tempfile.TemporaryDirectory() as d:
   c=Clock(9,0);t=Transport(c);self.run_case(d,c,t).execute(True)
   self.assertEqual(t.calls,['inspect']);self.assertEqual(list(Path(d).iterdir()),[])
 def test_review_latch_blocks_next_night_without_remote_actions(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/'review-required.json').write_text('{"reason":"synthetic device failure"}')
   c=Clock();t=Transport(c);self.assertIn('skipped',self.run_case(d,c,t).execute());self.assertEqual(t.calls,[])
 def test_two_successful_sessions_stop_until_analysis(self):
  with tempfile.TemporaryDirectory() as d:
   for i in range(2):(Path(d)/(str(i)+'.result.json')).write_text(json.dumps({'events':[{'stage':'comparison_complete'},{'stage':'accepted_sycl_and_schedules_restored'}]}))
   c=Clock();t=Transport(c);self.assertIn('skipped',self.run_case(d,c,t).execute());self.assertEqual(t.calls,[])
 def test_gpu_client_requires_pid_and_exact_guest_root(self):
  spec=importlib.util.spec_from_file_location('clients',Path(__file__).with_name('gpu-clients.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  self.assertTrue(m.expected_client([1234,77],77,(1,2),(1,2)))
  self.assertFalse(m.expected_client([1234,77],77,(1,3),(1,2)))
  self.assertFalse(m.expected_client([1234,78],77,(1,2),(1,2)))
if __name__=='__main__':unittest.main()
