import importlib.util
import json
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import mock_open, patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'b60-inference'))
spec = importlib.util.spec_from_file_location('matched', Path(__file__).with_name('matched-sycl.py'))
matched = importlib.util.module_from_spec(spec)
spec.loader.exec_module(matched)

class MatchedTrialTests(unittest.TestCase):
    def test_candidate_startup_failure_restores_without_retry(self):
        now = datetime(2026, 10, 10, 22, 20, tzinfo=ZoneInfo('America/Vancouver'))
        def guest(n, *args, **kwargs):
            if args[:2] == ('systemctl', 'is-active'):
                return 'failed' if n == 110 else 'inactive'
            if args[:2] == ('sh', '-c'):
                return '/private/runtime/lib'
            return ''
        with patch.object(matched, 'datetime') as date, \
             patch('builtins.open', mock_open(read_data=json.dumps({'collected_at': '2026-10-10T22:12:00-07:00'}))), \
             patch.object(matched, 'guest', side_effect=guest) as commands, \
             patch.object(matched, 'suite') as suite, \
             patch.object(matched, 'restore') as restore, \
             patch.object(matched.time, 'sleep'):
            date.now.return_value = now
            with self.assertRaisesRegex(RuntimeError, 'no retry'):
                matched.main()
            restore.assert_called_once_with()
            suite.assert_called_once_with('vulkan-pre', 'aster-llama.service')
            self.assertEqual(sum(c.args[1] == 'systemd-run' for c in commands.call_args_list), 1)

    def test_iommu_fault_pattern_uses_python_whitespace(self):
        import re
        self.assertIsNotNone(re.search(matched.FAULT, 'IOMMU: device translation fault', re.I))
        self.assertIsNone(re.search(matched.FAULT, 'default IOMMU domain type', re.I))

if __name__ == '__main__':
    unittest.main()
