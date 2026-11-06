import ast
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repair_remote_voice_authority as subject


SOURCE = Path(subject.__file__).read_text()


class RepairRemoteVoiceAuthorityTests(unittest.TestCase):
    def test_source_parses_and_names_exact_authorities(self):
        ast.parse(SOURCE)
        self.assertEqual(subject.LEGACY, "http://192.168.70.14:9130/v1/stt")
        self.assertEqual(
            subject.CANONICAL,
            "https://aster.elliottrook.com/voice/v3/v1/stt",
        )
        self.assertEqual(subject.HOST, "hermesagent")

    def test_environment_update_is_narrow_and_idempotent(self):
        original = "A=1\nASTER_REMOTE_VOICE_URL=" + subject.LEGACY + "\nB=2\n"
        expected = "A=1\nASTER_REMOTE_VOICE_URL=" + subject.CANONICAL + "\nB=2\n"
        self.assertEqual(subject.update_environment(original), expected)
        self.assertEqual(subject.update_environment(expected), expected)

    def test_unknown_or_duplicate_authority_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "voice-url-predecessor"):
            subject.update_environment("ASTER_REMOTE_VOICE_URL=http://unknown\n")
        with self.assertRaisesRegex(RuntimeError, "voice-url-cardinality"):
            subject.update_environment(
                "ASTER_REMOTE_VOICE_URL=" + subject.LEGACY + "\n"
                "ASTER_REMOTE_VOICE_URL=" + subject.LEGACY + "\n"
            )

    def test_checkpoint_rollback_and_no_secret_output_are_structural(self):
        self.assertIn("shutil.copy2(ENVIRONMENT, target / ENVIRONMENT.name)", SOURCE)
        self.assertIn("shutil.copy2(target / ENVIRONMENT.name, ENVIRONMENT)", SOURCE)
        self.assertIn('"credential_output": False', SOURCE)
        self.assertNotIn("ASTER_REMOTE_SPEECH_API_KEY", SOURCE)


if __name__ == "__main__":
    unittest.main()
