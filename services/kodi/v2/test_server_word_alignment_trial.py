import ast
from pathlib import Path
import unittest


class ServerWordAlignmentTrialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path(__file__).parent / 'tools/server_word_alignment_trial.py'
        cls.raw = cls.path.read_text()
        cls.tree = ast.parse(cls.raw)

    def test_existing_synthetic_audio_and_new_private_checkpoint_only(self):
        self.assertIn('aster-reader-epub-chapter-20261026/chapter.wav', self.raw)
        self.assertIn('aster-reader-word-alignment-20261026', self.raw)
        self.assertIn('0o700', self.raw); self.assertIn('0o600', self.raw)
        self.assertIn('O_EXCL', self.raw); self.assertIn('O_NOFOLLOW', self.raw)
        self.assertIn('os.geteuid() == 0', self.raw)

    def test_trial_cannot_render_speech_or_download_a_model(self):
        self.assertNotIn('urllib', self.raw)
        self.assertNotIn('/v1/tts', self.raw); self.assertNotIn('/v2/tts', self.raw)
        self.assertIn('local_files_only=True', self.raw)
        self.assertIn("tts_requests=0", self.raw)
        self.assertIn('os.nice(10)', self.raw)
        self.assertIn("word-alignment-time-budget", self.raw)

    def test_trial_requests_real_word_timestamps_and_exact_gate(self):
        self.assertIn('word_timestamps=True', self.raw)
        self.assertIn('align_exact(spoken, measured, duration)', self.raw)
        self.assertIn("condition_on_previous_text=False", self.raw)

    def test_output_is_private_and_console_summary_has_no_transcript(self):
        printed = [node for node in ast.walk(self.tree)
                   if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id == 'print']
        self.assertEqual(len(printed), 1)
        self.assertNotIn("'text'", ast.unparse(printed[0]))
        self.assertIn("recognizer-private.json", self.raw)


if __name__ == '__main__':
    unittest.main()
