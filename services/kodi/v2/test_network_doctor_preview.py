import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from build_network_doctor_preview import build, doctor_layout, menu_layout


class NetworkDoctorPreviewTests(unittest.TestCase):
    def test_exact_bundle_and_runtime_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'bundle';pin=build(root)
            value=json.loads((root/'manifest.json').read_text())
            self.assertEqual((value['kind'],len(value['files'])),
                             ('hp-network-preview.v6',7))
            self.assertTrue(value['books_doctor']);self.assertFalse(value['repairs'])
            spec=importlib.util.spec_from_file_location('doctor_preview',root/'default.py')
            module=importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules,xbmc=types.ModuleType('xbmc'),
                            xbmcgui=types.ModuleType('xbmcgui')):
                spec.loader.exec_module(module)
            module.verify(pin)

    def test_compact_menu_and_doctor_have_bounded_focus(self):
        menu=ET.fromstring(menu_layout());doctor=ET.fromstring(doctor_layout())
        self.assertEqual(menu.findtext(".//control[@id='1423']/label"),'Books narration')
        self.assertEqual(doctor.findtext('defaultcontrol'),'1434')
        self.assertEqual(doctor.findtext(".//control[@id='1435']/label"),'Back')
        self.assertFalse(menu.findall('.//onclick'));self.assertFalse(doctor.findall('.//onclick'))


if __name__=='__main__':unittest.main()
