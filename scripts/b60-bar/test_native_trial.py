import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parents[1]/'b60-inference'))
spec=importlib.util.spec_from_file_location('trial',Path(__file__).with_name('native-openvino-trial.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class RecoveryTests(unittest.TestCase):
 def test_candidate_telemetry_follows_candidate_pid(self):
  telemetry='vram_resident_kib=1000\ngpu_temp_pkg_millic=53000\ngpu_temp_vram_millic=52000\n'
  with patch.object(s,'CURRENT_UNIT','aster-b60-candidate.service'),patch.object(s,'run',side_effect=['[]','clean kernel']),patch.object(s,'guest',side_effect=['',telemetry]) as guest:
   s.kernel_gate()
   self.assertEqual(guest.call_args.args,(110,'sh','/run/b60-bar-telemetry.sh','aster-b60-candidate.service'))
 def test_zero_temperature_blocks_candidate(self):
  telemetry='vram_resident_kib=1000\ngpu_temp_pkg_millic=0\ngpu_temp_vram_millic=52000\n'
  with patch.object(s,'run',side_effect=['[]','clean kernel']),patch.object(s,'guest',side_effect=['',telemetry]):
   with self.assertRaises(AssertionError):s.kernel_gate()
 def test_watchdog_remains_armed_if_sycl_recovery_fails(self):
  with patch.object(s.prod,'restore_sycl',side_effect=RuntimeError('synthetic recovery failure')),patch.object(s,'run') as run:
   with self.assertRaises(RuntimeError):s.restore_after_trial()
   run.assert_not_called()
 def test_exact_sycl_recovery_precedes_disarm(self):
  seen=[]
  with patch.object(s.prod,'restore_sycl',side_effect=lambda:seen.append('sycl')),patch.object(s,'run',side_effect=lambda *args:seen.append(args)):
   s.restore_after_trial()
  self.assertEqual(seen,['sycl',('systemctl','stop','b60-openvino-restore.timer')])
 def test_empty_and_failed_kernel_logs_block_load(self):
  for log in ['', 'GPU HANG']:
   with patch.object(s,'run',side_effect=['[]',log]),patch.object(s,'guest') as guest:
    with self.assertRaises(AssertionError):s.kernel_gate()
    guest.assert_not_called()
 def test_active_backup_blocks_benchmark(self):
  with patch.object(s,'run',return_value='[{"type":"vzdump"}]'),patch.object(s,'guest') as guest:
   with self.assertRaisesRegex(AssertionError,'backup I/O'):s.kernel_gate()
   guest.assert_not_called()
if __name__=='__main__':unittest.main()
