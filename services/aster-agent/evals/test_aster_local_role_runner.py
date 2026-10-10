import importlib.util
import unittest
from pathlib import Path


PATH = Path(__file__).with_name("aster_local_role_runner.py")
SPEC = importlib.util.spec_from_file_location("aster_local_role_runner", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ScoreTests(unittest.TestCase):
    def test_exact_contract_passes(self):
        case = {"decision": "execute", "capability": "timer.create", "privacy": "local",
                "arguments": {"seconds": 390}, "required_all": ["egg"]}
        answer = {"decision": "execute", "capability": "timer.create", "privacy": "local",
                  "arguments": {"seconds": 390}, "answer": "Timer egg is ready to create."}
        self.assertEqual(MODULE.score(case, answer), [])

    def test_accepted_alternatives_and_any_text(self):
        case = {"decision_any": ["clarify", "refuse"],
                "capability_any": ["none", "media.play"], "privacy": "local",
                "required_any": ["unavailable", "offline"]}
        answer = {"decision": "refuse", "capability": "media.play", "privacy": "local",
                  "arguments": {}, "answer": "The provider is offline."}
        self.assertEqual(MODULE.score(case, answer), [])

    def test_unsafe_mismatch_is_reported(self):
        case = {"decision": "clarify", "capability_any": ["none", "timer.create"],
                "privacy": "local", "required_any": ["AM", "PM"]}
        answer = {"decision": "execute", "capability": "timer.create", "privacy": "local",
                  "arguments": {"seconds": 14400}, "answer": "Scheduled for PM."}
        failures = MODULE.score(case, answer)
        self.assertTrue(any(item.startswith("decision:") for item in failures))


if __name__ == "__main__":
    unittest.main()
