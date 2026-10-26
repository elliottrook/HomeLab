import importlib.util
from pathlib import Path
import unittest


SOURCE = Path(__file__).parent / 'skin.asterhome/tools/select_dispatch.py'


class SelectDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('aster_select_dispatch', SOURCE)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_series_command_requires_visible_verified_window_and_control(self):
        target = self.module.series_command_target
        self.assertEqual(target('13001', True, 300), 13001)
        self.assertEqual(target('13001', True, 314), 13001)
        for args in ((None, True, 300), ('13001', False, 300),
                     ('13001', True, 50), ('10000', True, 300),
                     ('14000', True, 300), ('13001x', True, 300)):
            self.assertIsNone(target(*args))


if __name__ == '__main__':
    unittest.main()
