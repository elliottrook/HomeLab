import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('summarize-matched-sycl.py')
PREFIX = 'matched-sycl-exclusive-20261010'

class MatchedReportTests(unittest.TestCase):
    def test_missing_results_never_claim_speed_gain(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.check_output([sys.executable,str(SCRIPT),'--exclusive','--evidence-root',directory],text=True)
            report = json.loads(result)
            self.assertFalse(report['complete'])
            self.assertNotIn('latency_reduction_percent',report)
            self.assertEqual(report['completed_repetitions']['sycl'],0)
            failed = subprocess.run([sys.executable,str(SCRIPT),'--exclusive','--evidence-root',directory,'--write-report'],capture_output=True,text=True)
            self.assertNotEqual(failed.returncode,0)
            self.assertFalse((Path(directory)/f'{PREFIX}-report.json').exists())

    def test_complete_comparison_is_immutable_and_discloses_lengths(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for label in ['vulkan-pre','sycl','vulkan-post']:
                latency = 1.0 if label != 'sycl' else 0.5
                tokens = 10 if label != 'sycl' else 8
                data = dict(suite_sha256='synthetic-fixture',median_latency_seconds=latency,pass_count=1,
                            results=[dict(id='synthetic',passed=True,elapsed_seconds=latency,
                                          usage=dict(completion_tokens=tokens))])
                for rep in range(1,6):
                    (root/f'{PREFIX}-{label}-{rep}.json').write_text(json.dumps(data))
            command=[sys.executable,str(SCRIPT),'--exclusive','--evidence-root',directory,'--write-report']
            report=json.loads(subprocess.check_output(command,text=True))
            self.assertTrue(report['complete'])
            self.assertEqual(report['request_speedup_factor'],2.0)
            self.assertEqual(report['latency_reduction_percent'],50.0)
            self.assertEqual(report['rows'][0]['sycl_completion_tokens'],[8])
            self.assertEqual(report['identical_completion_length_case_count'],0)
            self.assertIsNone(report['identical_completion_length_median_latency_reduction_percent'])
            self.assertEqual(len(report['evidence_sha256']),15)
            self.assertEqual((root/f'{PREFIX}-report.json').stat().st_mode & 0o777,0o600)
            repeat=subprocess.run(command,capture_output=True,text=True)
            self.assertNotEqual(repeat.returncode,0)
            self.assertIn('FileExistsError',repeat.stderr)
