import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


PATH = Path(__file__).with_name("measure_camera_stream.py")
SPEC = importlib.util.spec_from_file_location("measure_camera_stream", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CameraStreamMeasurementTests(unittest.TestCase):
    def test_cpu_math_is_bounded(self):
        self.assertEqual(MODULE.cpu_used((80, 100), (170, 200)), 10.0)
        with self.assertRaisesRegex(RuntimeError, "camera-cpu-sample"):
            MODULE.cpu_used((80, 100), (70, 90))

    def test_scope_is_exact_and_content_free(self):
        source = PATH.read_text()
        self.assertEqual(MODULE.SERVICE, "aster-camera.service")
        self.assertEqual(MODULE.CAMERA_WINDOW, 11134)
        self.assertIn('rpc("Input.Select")', source)
        self.assertIn('action("ActivateWindow(Home)")', source)
        self.assertIn('raise RuntimeError("camera-window-unstable")', source)
        for forbidden in ("Player.Open", "Player.Stop", "Player.GetItem",
                          "currentcontrol", "CameraImage", "latest.jpg",
                          "front_of_house"):
            self.assertNotIn(forbidden, source)

    def test_target_and_duration_fail_closed(self):
        with patch.object(MODULE.os, "uname") as uname:
            uname.return_value.nodename = "wrong-host"
            with self.assertRaisesRegex(RuntimeError, "camera-target"):
                MODULE.sample(10)
        with self.assertRaisesRegex(RuntimeError, "camera-duration"):
            MODULE.main(["--duration", "9"])


if __name__ == "__main__":
    unittest.main()
