import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

guard_spec=importlib.util.spec_from_file_location('guard',Path(__file__).parents[1]/'b60-inference/guard.py')
guard=importlib.util.module_from_spec(guard_spec);guard_spec.loader.exec_module(guard);sys.modules['guard']=guard
spec=importlib.util.spec_from_file_location('prod_controller',Path(__file__).with_name('production-sycl.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class ControllerTests(unittest.TestCase):
 def test_atomic_update_checks_both_hashes_and_no_overwrite_scratch(self):
  with patch.object(s,'guest') as guest:
   s.atomic_unit('source','old','new')
   code=guest.call_args_list[0].args[2]
   self.assertIn('os.O_EXCL',code)
   self.assertIn('os.replace(tmp,dst)',code)
   self.assertIn('sys.argv[3]',code)
   self.assertIn('sys.argv[4]',code)
   self.assertEqual(guest.call_args_list[1].args,('systemctl','daemon-reload'))
 def test_unarmed_watchdog_prevents_activation(self):
  with patch.object(s,'run',return_value='inactive'),patch.object(s,'guest') as guest:
   with self.assertRaises(AssertionError):s.activate('synthetic-test')
   guest.assert_not_called()
 def test_unknown_unit_prevents_destructive_rollback(self):
  import json
  with patch.object(s,'sha',side_effect=[s.OLD,guard.ACCEPTED_BINARY_SHA256,'unknown']),patch.object(s,'guest',return_value=json.dumps({'unit_sha256':'new'})),patch.object(s,'atomic_unit') as atomic:
   with self.assertRaisesRegex(AssertionError,'unknown unit'):s.rollback()
   atomic.assert_not_called()
 def test_sycl_recovery_rejects_unknown_unit_before_service_mutation(self):
  import json
  with patch.object(s,'guest',return_value=json.dumps({'unit_sha256':'accepted-sycl','volatile_dependencies':False})) as guest,patch.object(s,'sha',return_value='unexpected'):
   with self.assertRaisesRegex(AssertionError,'unit drift'):s.restore_sycl()
   self.assertEqual(guest.call_count,1)
if __name__=='__main__':unittest.main()
