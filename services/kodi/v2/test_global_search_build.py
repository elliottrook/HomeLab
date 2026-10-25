import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import xml.etree.ElementTree as ET
from build_global_search import build

class SearchBuildTests(unittest.TestCase):
    def test_immutable_deterministic_stage(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/'a',Path(folder)/'b'
            sha=build(a)
            self.assertEqual(sha,build(b))
            manifest=json.loads((a/'manifest.json').read_text())
            self.assertEqual(manifest['kind'],'hp-search-preview')
            self.assertEqual(len(manifest['files']),3)
            for row in manifest['files']:
                self.assertEqual(hashlib.sha256((a/row['path']).read_bytes()).hexdigest(),row['sha256'])
            with self.assertRaises(ValueError):build(a)

    def test_native_only_navigation_and_truthful_boundary(self):
        here=Path(__file__).resolve().parent
        source=(here/'search_native/default.py').read_text()
        self.assertNotIn('WindowXML',source)
        self.assertNotIn('Player.Open',source)
        self.assertNotIn('Playlist.Add',source)
        root=ET.parse(here/'search_native/overlay/custom_1127_search.xml').getroot()
        self.assertEqual(root.get('id'),'1127')
        controls={c.get('id'):c for c in root.findall('.//control') if c.get('id')}
        self.assertEqual(set(controls),{'10','20','30','40'})
        for control in controls.values():
            for direction in ('onleft','onright','onup','ondown'):
                self.assertIn(control.findtext(direction),controls)
        xml=ET.tostring(root).decode()
        self.assertIn('Not connected to search yet',xml)
        self.assertIn('no autoplay',xml)

    def test_details_stage_has_exact_members_and_native_back(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'details';build(output,details=True)
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['kind'],'hp-search-details')
            self.assertEqual(len(manifest['files']),6)
            root=ET.parse(output/'overlay/custom_1128_searchdetails.xml').getroot()
            self.assertEqual(root.get('id'),'1128')
            self.assertEqual(root.find(".//control[@id='10']/onclick").text,'Dialog.Close(11128)')
            self.assertEqual(root.find(".//control[@id='10']/align").text,'center')
            self.assertIn('24-music-artist.png',(output/'default.py').read_text())

    def test_rejected_duplicate_cannot_clear_live_window_properties(self):
        home=Mock()
        path=Path(__file__).resolve().parent/'search_native/default.py'
        spec=importlib.util.spec_from_file_location('search_preview_test',path)
        module=importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules',xbmc=Mock(),xbmcgui=SimpleNamespace(Window=lambda _:home)):
            spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            module.DIRECTORY=Path(folder)
            with patch.object(module.os,'uname',return_value=SimpleNamespace(nodename='AsterTV')):
                with patch.object(module.fcntl,'flock',side_effect=BlockingIOError):
                    module.main()
        home.clearProperty.assert_not_called()

if __name__=='__main__':unittest.main()
