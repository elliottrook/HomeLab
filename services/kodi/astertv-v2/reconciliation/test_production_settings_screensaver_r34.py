import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name(
    "apply_production_settings_screensaver_r34_fix.py")
SPEC = importlib.util.spec_from_file_location("r34", SCRIPT)
R34 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(R34)


class ProductionSettingsScreensaverR34Tests(unittest.TestCase):
    def test_dispatch_adds_direct_settings_paths(self):
        source = (Path(__file__).parent / "payload/skin.asterhome/tools/select_dispatch.py")
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "select_dispatch.py"
            candidate.write_bytes(source.read_bytes())
            original = R34.SELECT_DISPATCH
            R34.SELECT_DISPATCH = candidate
            try:
                patched = R34.patched_dispatch().decode()
            finally:
                R34.SELECT_DISPATCH = original
        self.assertIn("if focus_id == 9005:", patched)
        self.assertIn("ActivateWindow(Settings)", patched)
        self.assertIn("ActivateWindow(InterfaceSettings)", patched)
        self.assertIn("ActivateWindow(PlayerSettings)", patched)
        self.assertIn("ActivateWindow(ServiceSettings)", patched)
        compile(patched, "select_dispatch.py", "exec")

    def test_dispatch_source_has_direct_search_paths(self):
        source = (Path(__file__).parent
                  / "payload/skin.asterhome/tools/select_dispatch.py").read_text()
        self.assertIn("window_id == 10000 and focus_id == 135", source)
        self.assertIn("aster-global-search-ui22", source)
        self.assertIn("focus_id == 139", source)
        self.assertIn("header_search.py", source)

    def test_screensaver_default_and_profile_select_aster(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "settings.xml"
            candidate.write_text(
                '<settings><setting id="presentation" type="labelenum" '
                'label="Idle presentation" values="black|aster" '
                'default="black" /></settings>')
            original = R34.SAVER_SETTINGS
            R34.SAVER_SETTINGS = candidate
            try:
                patched = R34.patched_saver_settings().decode()
            finally:
                R34.SAVER_SETTINGS = original
        self.assertIn('default="aster"', patched)
        self.assertIn(">aster</setting>", R34.saver_profile().decode())

    def test_patch_is_fail_closed_on_changed_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "select_dispatch.py"
            candidate.write_text("print('changed')\n")
            original = R34.SELECT_DISPATCH
            R34.SELECT_DISPATCH = candidate
            try:
                with self.assertRaisesRegex(RuntimeError, "source mismatch"):
                    R34.patched_dispatch()
            finally:
                R34.SELECT_DISPATCH = original


if __name__ == "__main__":
    unittest.main()
