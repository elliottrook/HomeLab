import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def module(path):
    spec = importlib.util.spec_from_file_location("m5n_apply_test", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


APPLY = module(ROOT / "apply_jen_news_icons.py")


class JenNewsIconTests(unittest.TestCase):
    def fixture(self):
        controls = []
        for control_id, _, _, between in APPLY.PILLS:
            controls.append(
                f'<control type="button" id="{control_id}"><label>L{control_id}</label>'
                f'<onclick>Action{control_id}</onclick><onleft>{control_id - 1}</onleft>'
                f'<onright>{control_id + 1}</onright><ondown>500</ondown>'
                f'<textoffsetx>0</textoffsetx>{between}'
                f'<onup>{control_id}</onup></control>'
            )
        return ("<window><controls>" + "".join(controls) + "</controls></window>").encode()

    def test_exact_four_pills_gain_contained_plain_compass(self):
        result = APPLY.patch_news(self.fixture()).decode()
        self.assertEqual(result.count("aster-compass-128.png"), 4)
        self.assertEqual(result.count("<textoffsetx>20</textoffsetx>"), 4)
        for control_id, _, _, _ in APPLY.PILLS:
            self.assertIn(f'id="{control_id + 9000}"', result)

    def test_routes_labels_and_focus_graph_are_unchanged(self):
        before = ET.fromstring(self.fixture())
        after = ET.fromstring(APPLY.patch_news(self.fixture()))
        fields = ("label", "onclick", "onleft", "onright", "onup", "ondown")
        for control_id, _, _, _ in APPLY.PILLS:
            old = before.find(f".//control[@id='{control_id}']")
            new = after.find(f".//control[@id='{control_id}']")
            self.assertIsNotNone(old); self.assertIsNotNone(new)
            self.assertEqual({name: old.findtext(name) for name in fields},
                             {name: new.findtext(name) for name in fields})

    def test_transform_fails_closed_on_anchor_drift(self):
        with self.assertRaisesRegex(RuntimeError, "news-pill-anchor"):
            APPLY.patch_news(b"<window />")

    def test_installer_is_host_hash_idle_and_rollback_pinned(self):
        source = (ROOT / "install_jen_news_icons.py").read_text()
        for token in ("AsterTV-Jen", "Player.GetActivePlayers", "news-base-drift",
                      "checkpoint-mismatch", "checkpoint-host-mismatch",
                      "rollback-hash-mismatch",
                      "After=astertv-v3-m4y-jen.service", "Before=kodi.service"):
            self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
