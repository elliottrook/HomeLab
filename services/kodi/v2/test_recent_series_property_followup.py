"""Tests for the resilient Recently Added series route successor."""

import json
import unittest
from unittest.mock import patch

import recent_series_property_followup as subject


class RecentSeriesPropertyTests(unittest.TestCase):
    def test_exact_hp_successor(self):
        launcher_raw = (b"def launch(window, control, container, xbmc):\n"
            b"    identity=selected_show(window,control,xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBTYPE'),\n"
            b"        xbmc.getInfoLabel('Container('+str(container)+').ListItem.DBID'),\n"
            b"        False)\n")
        family_raw = json.dumps({'skin': {
            'tools/aster_v2_series.py': subject.sha(launcher_raw)}}).encode()
        predecessors = dict(subject.PREDECESSORS)
        predecessors['launcher.py'] = subject.sha(launcher_raw)
        predecessors['family.json'] = subject.sha(family_raw)
        with patch.dict(subject.PREDECESSORS, predecessors, clear=True):
            launcher = subject.launcher(launcher_raw)
            family = subject.family(family_raw, launcher)
        self.assertIn(b'Property(AsterDbId)', launcher)
        self.assertEqual(json.loads(family)['skin']['tools/aster_v2_series.py'],
                         subject.sha(launcher))

    def test_plugin_transform_adds_property(self):
        raw = (b"def add(item, row):\n"
               b"            item.getVideoInfoTag().setDbId(row['id'])\n")
        with patch.dict(subject.PREDECESSORS, {'plugin.py': subject.sha(raw)}):
            candidate = subject.plugin(raw)
        self.assertIn(b"item.setProperty('AsterDbId', str(row['id']))", candidate)


if __name__ == '__main__':
    unittest.main()
