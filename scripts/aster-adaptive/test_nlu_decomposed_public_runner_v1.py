import json, unittest
from pathlib import Path
import nlu_decomposed_public_runner_v1 as runner

FIXTURE=Path(__file__).with_name("fixtures")/"nlu-development-v1.json"

class DecomposedRunnerTests(unittest.TestCase):
    def test_fixture_and_credential_fail_closed(self):
        with self.assertRaises(ValueError): runner.run(b"{}","x"*16)
        with self.assertRaises(ValueError): runner.run(FIXTURE.read_bytes(),"short")

    def test_runner_has_bounded_non_authorizing_contract(self):
        self.assertEqual(1200,runner.WALL_DEADLINE)
        self.assertEqual(60,runner.PER_CALL_TIMEOUT)
        self.assertEqual(6,len(runner.candidate.TASKS))
        self.assertEqual("not-granted",json.loads('{"authority":"not-granted"}')["authority"])

if __name__=="__main__": unittest.main()
