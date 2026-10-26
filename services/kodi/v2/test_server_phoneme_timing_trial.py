import ast
import hashlib
from pathlib import Path
import unittest


class ServerPhonemeTimingTrialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path(__file__).parent / 'tools/server_phoneme_timing_trial.py'
        cls.raw = cls.path.read_text(); cls.tree = ast.parse(cls.raw)

    def test_text_identity_is_pinned_and_synthetic(self):
        module = {}
        for node in self.tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                try: exec(compile(ast.Module([node], []), str(self.path), 'exec'), module)
                except Exception: pass
        self.assertEqual(hashlib.sha256(module['TEXT'].encode()).hexdigest(),
                         module['TEXT_SHA'])
        self.assertIn("real_book_access=False", self.raw)

    def test_uses_existing_canonical_model_once_without_network_or_service_change(self):
        self.assertIn("('bm_daniel', 'en-gb', .95)", self.raw)
        self.assertIn('verify_assets()', self.raw)
        self.assertIn('create_timed(', self.raw)
        self.assertIn("model_invocations'] = 1", self.raw)
        self.assertNotIn('urllib', self.raw); self.assertNotIn('requests', self.raw)
        self.assertNotIn('systemctl restart', self.raw)
        self.assertIn('service_pid_unchanged', self.raw)
        self.assertIn('os.nice(10)', self.raw)

    def test_exact_phoneme_gate_and_private_output_are_mandatory(self):
        self.assertIn('align_phonemes(TEXT, phonemes, measured, duration)', self.raw)
        self.assertIn('0o700', self.raw); self.assertIn('0o600', self.raw)
        self.assertIn('O_EXCL', self.raw); self.assertIn('O_NOFOLLOW', self.raw)
        self.assertIn('timings-private.json', self.raw)
        self.assertIn('cues-private.json', self.raw)
        self.assertIn('plan-private.json', self.raw)
        self.assertLess(self.raw.index("timings-private.json"),
                        self.raw.index('align_phonemes(TEXT, phonemes, measured, duration)'))

    def test_console_summary_excludes_text_phonemes_and_timings(self):
        printed = [node for node in ast.walk(self.tree)
                   if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id == 'print']
        self.assertEqual(len(printed), 1)
        value = ast.unparse(printed[0])
        for forbidden in ('TEXT', 'phonemes', 'measured', 'timings'):
            self.assertNotIn(forbidden, value)


if __name__ == '__main__':
    unittest.main()
