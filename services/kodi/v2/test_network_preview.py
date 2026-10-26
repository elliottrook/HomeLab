import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from build_network_preview import build,layout

HERE=Path(__file__).parent


class NetworkPreviewTests(unittest.TestCase):
    def test_manifest_members_pin_and_drift(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()/'bundle';pin=build(root)
            manifest=json.loads((root/'manifest.json').read_text())
            self.assertEqual(len(manifest['files']),4)
            self.assertTrue(manifest['network_probes']);self.assertTrue(manifest['explicit_service_checks'])
            self.assertFalse(manifest['network_changes'])
            spec=importlib.util.spec_from_file_location('network_preview',root/'default.py')
            module=importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules,xbmc=types.ModuleType('xbmc'),xbmcgui=types.ModuleType('xbmcgui')):
                spec.loader.exec_module(module)
            module.verify(pin)
            with self.assertRaises(ValueError):module.verify('0'*64)
            path=root/'network_diagnostics.py';path.write_bytes(path.read_bytes()+b'\n')
            with self.assertRaises(ValueError):module.verify(pin)
            with self.assertRaises(FileExistsError):build(root)

    def test_layout_fonts_focus_and_no_http_images_or_auto_actions(self):
        root=ET.fromstring(layout())
        fonts={n.text for n in ET.parse(HERE.parent/'skin.asterhome/1080i/Font.xml').findall('.//name')}
        self.assertTrue(all(n.text in fonts for n in root.findall('.//font')))
        for n,right in ((200,'203'),(203,'201'),(201,'200')):
            control=root.find(".//control[@id='%d']" % n)
            self.assertEqual(control.findtext('onright'),right)
            self.assertEqual(control.findtext('onup'),'noop')
        self.assertFalse(root.findall('.//onclick'))
        self.assertNotIn('http',layout().decode())
        ids=[n.get('id') for n in root.findall('.//control') if n.get('id')]
        self.assertEqual(len(ids),len(set(ids)))

    def test_runtime_is_manual_read_only_and_offline_demo_is_explicit(self):
        script=(HERE/'network_preview/default.py').read_text()
        for banned in ('Player.Open','Player.Stop','PlayMedia','ActivateWindow(',
            'socket.connect','urlopen','call_service','nmcli','ifconfig','systemctl','assert '):
            self.assertNotIn(banned,script)
        self.assertIn('network settings were NOT changed',script)
        self.assertIn("sys.argv[2]!='offline-demo'",script)
        self.assertIn('elif self.check_services:self.render_services()',script)
        self.assertIn('if demo:return',script)

    def test_entry_list_is_bounded_and_honest_about_truncation(self):
        spec=importlib.util.spec_from_file_location('network_entry',HERE/'network_preview/default.py')
        module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,xbmc=types.ModuleType('xbmc'),xbmcgui=types.ModuleType('xbmcgui')):
            spec.loader.exec_module(module)
        self.assertEqual(module.display_lines([],'Unavailable'),'Unavailable')
        self.assertEqual(module.display_lines(['a','b'],'empty'),'a\nb')
        self.assertEqual(module.display_lines(list('abcdef'),'empty'),'a\nb\nc\nd\n2 more configured entries')
