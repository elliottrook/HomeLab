import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from evaluation_lease_entrypoint import main


class EntryPointTests(unittest.TestCase):
    def test_default_entrypoint_is_inert_without_reading_intent(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main([
                "--phase", "acquire", "--state", "/absent/state",
                "--intent", "/absent/intent",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue()),
                         {"effects": "disabled", "state": "source-only"})

    def test_effectful_path_requires_strict_intent(self):
        with self.assertRaises(Exception):
            # The effect flag is deliberately not used here; this only proves
            # the strict loader rejects malformed input before any adapter call.
            from evaluation_lease_entrypoint import load_intent
            path = Path("/tmp/stream-a-invalid-intent.json")
            path.write_text("[]\n")
            try:
                load_intent(path)
            finally:
                path.unlink()


if __name__ == "__main__":
    unittest.main()
