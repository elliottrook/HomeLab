import ast
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent


class InterpreterCustodyRepairTests(unittest.TestCase):
    def test_repair_is_checkpointed_inert_and_exact(self):
        source = (HERE / "repair_interpreter_custody.py").read_text()
        ast.parse(source)
        for token in ("FAILED_ATTEMPT_NOT_RETAINED", "GUEST_CHECKPOINT",
                      "STATIC_VALIDATION", '"booking_created": False',
                      '"workload_started": False'):
            self.assertIn(token, source)
        self.assertNotIn("reserve --", source)
        self.assertNotIn("systemctl start", source)

    def test_benchmark_accepts_only_exact_runtime_target(self):
        source = (HERE / "ebook_word_alignment_benchmark.py").read_text()
        self.assertIn('PYTHON_TARGET = Path("/usr/bin/python3.13")', source)
        self.assertIn("if resolved != pinned", source)
        self.assertIn("PINNED_RUNTIME_CUSTODY", source)


if __name__ == "__main__":
    unittest.main()
