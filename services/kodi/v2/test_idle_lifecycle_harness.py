import ast
from pathlib import Path
import unittest

class LifecycleHarnessTests(unittest.TestCase):
    def test_checks_survive_optimized_python_and_scope_is_narrow(self):
        source = (Path(__file__).parent/'tools/live_idle_lifecycle.py').read_text()
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(n, ast.Assert) for n in ast.walk(tree)))
        for forbidden in ('Player.Open', 'Player.Stop', 'PlayMedia', 'getControl(', 'subprocess', 'Password'):
            self.assertNotIn(forbidden, source)
        self.assertIn('trial-restore-pending.json', source)
        self.assertIn("value=DIM", source)
        self.assertIn("if __name__ == '__main__': main()", source)
        self.assertNotIn('result.update(passed=True', source)
        self.assertIn("result.update(passed=False, code=", source)
        self.assertGreater(source.index("guard.snapshot() == av"), source.index("value=DIM"))

    def test_camera_expiry_trial_never_requests_images(self):
        source = (Path(__file__).parent/'tools/check_camera_expiry.py').read_text()
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(n, ast.Assert) for n in ast.walk(tree)))
        self.assertNotIn('latest.jpg', source)
        self.assertNotIn("request('/view/stop'", source)
        self.assertIn('300 - elapsed', source)
