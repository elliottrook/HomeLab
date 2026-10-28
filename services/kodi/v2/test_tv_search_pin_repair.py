import importlib.util
import json
import tempfile
import types
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "repair_tv_search_pins", HERE / "tools/repair_tv_search_pins.py")
REPAIR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPAIR)


class TvSearchPinRepairTests(unittest.TestCase):
    def test_repairs_only_stale_tv_and_search_pins(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "addons/script.asterruntime"
            skin = root / "addons/skin.asterhome"
            series_dir = runtime / "aster-series-preview24"
            search_dir = runtime / "aster-global-search-ui22"
            series_dir.mkdir(parents=True)
            (search_dir / "resources/lib").mkdir(parents=True)
            skin.joinpath("tools").mkdir(parents=True)

            series_manifest = {"component": "aster-series-preview24",
                               "files": [{"path": str(i), "bytes": 1,
                                          "sha256": "0" * 64} for i in range(8)]}
            (series_dir / "manifest.json").write_text(
                json.dumps(series_manifest, indent=2, sort_keys=True) + "\n")
            series_pin = REPAIR.sha((series_dir / "manifest.json").read_bytes())
            stale = "a" * 64
            launcher = skin / "tools/aster_v2_series.py"
            launcher.write_text("MANIFEST_SHA='" + stale + "'\n")
            handoff = search_dir / "resources/lib/search_handoff.py"
            handoff.write_text("SERIES_SHA='" + "b" * 64 + "'\n")
            search_manifest = {"files": [{"path": "resources/lib/search_handoff.py",
                                          "bytes": len(handoff.read_bytes()),
                                          "sha256": REPAIR.sha(handoff.read_bytes())}]}
            (search_dir / "manifest.json").write_text(
                json.dumps(search_manifest, indent=2, sort_keys=True) + "\n")
            family = {"components": {
                "aster-series-preview24": {"manifest_sha256": series_pin},
                "aster-global-search-ui22": {"manifest_sha256": "c" * 64}},
                "skin": {"tools/aster_v2_series.py": REPAIR.sha(launcher.read_bytes())}}
            (runtime / "family-manifest.json").write_text(
                json.dumps(family, indent=2, sort_keys=True) + "\n")

            REPAIR.RUNTIME = runtime
            REPAIR.ROOT = root / "addons"
            REPAIR.SERIES = series_dir / "manifest.json"
            REPAIR.LAUNCHER = launcher
            REPAIR.SEARCH = search_dir
            REPAIR.HANDOFF = handoff
            REPAIR.SEARCH_MANIFEST = search_dir / "manifest.json"
            REPAIR.FAMILY = runtime / "family-manifest.json"
            REPAIR.CHECKPOINT = root / "checkpoint"
            original_uname = REPAIR.os.uname
            REPAIR.os.uname = lambda: types.SimpleNamespace(nodename="AsterTVProd")
            try:
                REPAIR.main()
            finally:
                REPAIR.os.uname = original_uname

            self.assertIn(series_pin, launcher.read_text())
            self.assertIn(series_pin, handoff.read_text())
            self.assertEqual(json.loads((REPAIR.CHECKPOINT / "state.json").read_text())["state"],
                             "installed")


if __name__ == "__main__":
    unittest.main()
