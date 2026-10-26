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
        self.assertEqual(set(controls),{'10','20','30','40','50','51'})
        for control in controls.values():
            for direction in ('onleft','onright','onup','ondown'):
                self.assertIn(control.findtext(direction),controls)
        xml=ET.tostring(root).decode()
        self.assertIn('Not connected to search yet',xml)
        self.assertIn('no autoplay',xml)
        self.assertEqual(controls['50'].findtext('label'),'Search library')
        self.assertEqual(controls['51'].findtext('label'),'Search catalogue')
        self.assertEqual(controls['51'].findtext('onclick'),'RunScript(script.asterseerr)')

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

    def test_handoff_native_window_and_small_home_entry(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'handoff';build(output,details=True,handoff=True)
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual((manifest['kind'],len(manifest['files'])),('hp-search-playerlinks',8))
            search=ET.parse(output/'overlay/custom_1127_search.xml').getroot()
            self.assertEqual(search.get('type'),'window')
            home=ET.parse(output/'overlay/Home.xml').getroot()
            button=home.find(".//control[@id='135']")
            self.assertEqual(button.findtext('width'),'110');self.assertEqual(button.findtext('height'),'46')
            self.assertEqual(home.findtext(".//control[@id='134']/onright"),'135')
            self.assertEqual(button.findtext('onleft'),'134')
            self.assertEqual(button.findtext('align'),'center')
            self.assertEqual(button.findtext('onclick'),'RunScript(/storage/.aster-staging/aster-global-search-ui5/default.py)')
            details=ET.parse(output/'overlay/custom_1128_searchdetails.xml').getroot()
            self.assertEqual(details.findtext(".//control[@id='11']/onclick"),'SetProperty(AsterSearch.Command,open,home)')

    def test_artist_successor_has_back_interception_and_exact_predecessor(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'artist';build(output,True,True,'aster-global-search-ui7')
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(len(manifest['files']),9);self.assertTrue(manifest['artist_albums'])
            self.assertEqual(manifest['previous_manifest_sha256'],'def37da8481dd0b53cd2650056ddeee94656ba14b21b83d0b73bafeda5fc9a6c')
            search=ET.parse(output/'overlay/custom_1127_search.xml').getroot()
            for identity in ('10','20','30','40'):
                self.assertEqual(search.findtext(".//control[@id='"+identity+"']/onback"),'SetProperty(AsterSearch.Command,back,home)')
            self.assertEqual(search.findtext(".//control[@id='40']/onclick"),'SetProperty(AsterSearch.Command,back,home)')

    def test_native_artist_successor_uses_history_not_back_override(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'artist';build(output,True,True,'aster-global-search-ui9')
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(len(manifest['files']),10);self.assertEqual(manifest['artist_native_window'],11129)
            artist=ET.parse(output/'overlay/custom_1129_artistalbums.xml').getroot()
            self.assertEqual((artist.get('id'),artist.get('type')),('1129','window'))
            self.assertEqual(artist.findtext('previouswindow'),'1127')
            self.assertIsNone(artist.find('onload'));self.assertIsNone(artist.find('onunload'))
            self.assertEqual(artist.findtext(".//control[@id='40']/onclick"),'Action(Back)')
            self.assertNotIn('onback',(output/'overlay/custom_1127_search.xml').read_text())
            dispatch=(output/'overlay/select_dispatch.py').read_text()
            self.assertIn('getCurrentWindowId() in (11127, 11129)',dispatch)
            self.assertIn('Window(xbmcgui.getCurrentWindowId()).getFocusId()',dispatch)

if __name__=='__main__':unittest.main()
