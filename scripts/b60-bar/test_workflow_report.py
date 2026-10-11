import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('workflow_report',Path(__file__).with_name('summarize-workflow-sycl.py'))
report=importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)

class WorkflowReportTests(unittest.TestCase):
    def test_decode_profile_requires_sustained_completion_length(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            samples=[dict(phase=kind,control_role='warmup' if rep==0 else 'measured',correct=True,
                          seconds=1,tokens=76 if kind=='prefill' else 12,tokens_per_second=12,
                          rate_source='server_predicted_per_second') for rep in range(6) for kind in ['prefill','decode']]
            data=dict(fixture='b60-tg128-warm',health_passed=True,prompt_sha256='identical',samples=samples)
            (root/'run-vulkan-pre-b60-tg128-warm.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(AssertionError,'sustained'): report.summarize(root,'run','decode')
    def fixture(self,root,phase,correct=True,source='server_predicted_per_second'):
        for fixture in report.FIXTURES:
            samples=[]
            for rep in range(6):
                for kind in ['prefill','decode']:
                    samples.append(dict(phase=kind,control_role='warmup' if rep==0 else 'measured',correct=correct,
                                        seconds=1 if phase=='sycl' else 2,tokens=(8000 if fixture=='aster-context-8k' else 2048) if kind=='prefill' else 40,
                                        tokens_per_second=40 if phase=='sycl' else 20,rate_source=source))
            (root/f'run-{phase}-{fixture}.json').write_text(json.dumps(dict(fixture=fixture,health_passed=True,
                                                                         prompt_sha256='identical',samples=samples)))
    def test_missing_is_not_a_complete_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            result=report.summarize(Path(directory),'run')
            self.assertFalse(result['complete'])
            self.assertEqual(result['fixtures'],{})
    def test_complete_reports_request_and_decode_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for phase in ['vulkan-pre','sycl','vulkan-post']: self.fixture(root,phase)
            result=report.summarize(root,'run')
            self.assertTrue(result['complete'])
            self.assertEqual(len(result['evidence_sha256']),6)
            for row in result['fixtures'].values():
                self.assertEqual(row['request_latency_reduction_percent'],50)
                self.assertEqual(row['server_decode_improvement_percent'],100)
    def test_fallback_rate_never_claims_decode_improvement(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for phase in ['vulkan-pre','sycl','vulkan-post']: self.fixture(root,phase,source='completion_tokens_over_request_seconds')
            result=report.summarize(root,'run')
            self.assertNotIn('server_decode_improvement_percent',result['fixtures'][report.FIXTURES[0]])
    def test_correctness_failure_cannot_be_reported_as_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            self.fixture(root,'vulkan-pre',correct=False)
            with self.assertRaisesRegex(AssertionError,'correctness'): report.summarize(root,'run')
