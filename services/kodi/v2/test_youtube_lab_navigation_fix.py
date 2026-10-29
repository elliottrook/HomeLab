"""Tests for the current lab candidate's YouTube button repair."""

import unittest
import xml.etree.ElementTree as ET

from youtube_lab_navigation_fix import BACK_HELPER, ROUTE_BUTTONS, ROUTE_FOCUS, ROUTES, ROWS, add_route_focus_to_live, correct_watch_later_live, transform


class YouTubeLabNavigationTests(unittest.TestCase):
    def fixture(self):
        root = ET.Element("window")
        controls = ET.SubElement(root, "controls")
        for identity in ROUTE_BUTTONS:
            button = ET.SubElement(controls, "control", {"id":str(identity)})
            ET.SubElement(button, "label").text = "Old label"
            ET.SubElement(button, "onclick").text = (
                'ActivateWindow(Videos,"plugin://plugin.video.youtube/'
                f'special/{identity}?category_label=Test",return)')
        for identity in (9305, 9404):
            button = ET.SubElement(controls, "control", {"id":str(identity)})
            ET.SubElement(button, "onclick").text = BACK_HELPER
        button = ET.SubElement(controls, "control", {"id":"9000"})
        ET.SubElement(button, "onclick").text = "Action(Back)"
        for identity in ROWS:
            heading = ET.SubElement(controls, "control", {"type":"label"})
            ET.SubElement(heading, "label").text = "Old heading"
            panel = ET.SubElement(controls, "control", {"id":str(identity)})
            ET.SubElement(panel, "content").text = "plugin://plugin.video.youtube/old"
        return ET.tostring(root)

    def test_routes_stay_in_videos_and_back_returns_to_youtube(self):
        root = ET.fromstring(transform(self.fixture()))
        for identity in ROUTE_BUTTONS:
            action = root.find(f".//control[@id='{identity}']/onclick")
            expected = (ROUTES[identity][1] if identity in ROUTES else
                        f"plugin://plugin.video.youtube/special/{identity}?category_label=Test")
            self.assertEqual(action.text, f"Container.Update({expected})")
            actions = root.findall(f".//control[@id='{identity}']/onclick")
            if identity in ROUTES:
                self.assertEqual([item.text for item in actions],
                                 [f"Container.Update({expected})",
                                  f"RunScript({ROUTE_FOCUS},{expected})"])
            else:
                self.assertEqual(len(actions), 1)
        for identity, (heading, route) in ROWS.items():
            self.assertEqual(root.find(f".//control[@id='{identity}']/content").text,
                             route)
        actions = root.findall(".//control[@id='9000']/onclick")
        self.assertEqual([action.text for action in actions],
                         ["Action(Back)", BACK_HELPER])
        self.assertEqual(actions[1].get("condition"),
                         "String.Contains(Container.FolderPath,plugin.video.youtube)")

    def test_refuses_unrecognized_predecessor(self):
        with self.assertRaises(ValueError):
            transform(b"<window><controls /></window>")

    def test_live_upgrade_is_pinned_and_single_use(self):
        raw = transform(self.fixture())
        with self.assertRaisesRegex(ValueError, "unexpected installed"):
            add_route_focus_to_live(raw)
        root = ET.fromstring(raw)
        for identity in ROUTES:
            button = root.find(f".//control[@id='{identity}']")
            button.remove(button.findall("onclick")[1])
        upgraded = add_route_focus_to_live(ET.tostring(root))
        self.assertEqual(len(ET.fromstring(upgraded).findall(".//control[@id='9301']/onclick")), 2)

    def test_watch_later_uses_online_playlist(self):
        root = ET.fromstring(transform(self.fixture()))
        old = "plugin://plugin.video.youtube/kodion/watch_later/list"
        new = ROUTES[9303][1]
        for identity in (9303, 9403):
            actions = root.findall(f".//control[@id='{identity}']/onclick")
            actions[0].text = f"Container.Update({old})"
            actions[1].text = f"RunScript({ROUTE_FOCUS},{old})"
        root.find(".//control[@id='9532']/content").text = old
        updated = ET.fromstring(correct_watch_later_live(ET.tostring(root)))
        self.assertEqual(updated.find(".//control[@id='9532']/content").text, new)
        self.assertEqual(updated.find(".//control[@id='9303']/onclick").text,
                         f"Container.Update({new})")


if __name__ == "__main__":
    unittest.main()
