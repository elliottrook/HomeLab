import ast,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
import xml.etree.ElementTree as ET
from build_music_integration import BASE,BEFORE,build,transformed
import json
import types
from integration_handoff import handoff,restore_focus,RETURN,open_route


class IntegrationTests(unittest.TestCase):
    def generated_load(self,*,stale=False,current=11113):
        kodi=Mock();gui=Mock();window=Mock();props={}
        window.getProperty.side_effect=lambda key:props.get(key,'')
        window.setProperty.side_effect=lambda key,value:props.__setitem__(key,value)
        gui.Window.return_value=window;gui.getCurrentWindowId.return_value=current
        restore=Mock(return_value=False)
        modules={'hub_data':types.SimpleNamespace(kodi_rpc=Mock()),
            'aster_v2_music':types.SimpleNamespace(handoff=Mock(),restore_focus=restore),
            'xbmc':kodi,'xbmcgui':gui,'xbmcvfs':Mock()}
        with patch.dict('sys.modules',modules):
            namespace={'__name__':'generated_music_test'}
            exec(compile(transformed()['tools/music_data.py'],'generated_music.py','exec'),namespace)
            def query(*args):
                if stale:props['AsterMusic.LoadRequest']='newer-load'
                return ([{}],1)
            namespace['music_query']=query
            namespace['music_row']=lambda *args:dict(title='Example',detail='',summary='',id=12,file='',thumb='',fanart='')
            namespace['main']('home')
        return kodi,window,props,restore

    def test_completed_load_publishes_generation_and_only_then_accepts_selection(self):
        kodi,window,props,restore=self.generated_load()
        self.assertEqual(props['AsterMusic.LoadReady'],'true')
        self.assertEqual(props['AsterMusic.LoadGeneration'],props['AsterMusic.LoadRequest'])
        restore.assert_called_once();window.getControl.return_value.addItems.assert_called_once()
        kodi.executebuiltin.assert_called_once_with('Control.SetFocus(500,0,absolute)')

    def test_older_async_load_cannot_publish_or_restore_focus(self):
        kodi,window,props,restore=self.generated_load(stale=True)
        window.getControl.assert_not_called();restore.assert_not_called();kodi.executebuiltin.assert_not_called()
        self.assertEqual(props['AsterMusic.LoadReady'],'false')
        self.assertNotIn('AsterMusic.LoadGeneration',props)

    def test_background_load_does_not_steal_another_window_focus(self):
        kodi,window,props,restore=self.generated_load(current=11116)
        self.assertEqual(props['AsterMusic.LoadReady'],'true')
        restore.assert_not_called();kodi.executebuiltin.assert_not_called()

    def test_build_preserves_recently_added_five_header_controls_and_hero_shuffle(self):
        before={name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in BEFORE}
        files=transformed();self.assertEqual(len(files),8)
        self.assertEqual(before,BEFORE)
        home=ET.fromstring(files['1080i/custom_1113_music.xml'])
        loads=[node.text for node in home.findall('onload')]
        self.assertEqual(loads[:2],['ClearProperty(AsterMusic.LoadReady,11113)', 'ClearProperty(AsterMusic.LoadRequest,11113)'])
        self.assertTrue(any('music_data.py,home' in command for command in loads))
        self.assertEqual(home.find(".//param[@name='heading']").get('value'),'Recently Added')
        root=ET.fromstring(files['1080i/IncludesMusic.xml']);edge=350
        for identity in range(110,115):
            node=root.find(f".//control[@id='{identity}']");left=int(node.findtext('left'))
            self.assertGreater(left,edge);edge=left+200
            self.assertLess(edge,1714)
            self.assertEqual(node.findtext('enable'),'String.IsEqual(Window.Property(AsterMusic.LoadReady),true)')
        self.assertEqual(root.find(".//control[@id='500']/enable").text,'String.IsEqual(Window.Property(AsterMusic.LoadReady),true)')
        hero=root.find(".//control[@id='115']")
        self.assertEqual(hero.findtext('top'),'455')
        self.assertEqual(hero.findtext('visible'),'Window.IsActive(11113)')
        self.assertEqual(hero.findtext('onclick'),'RunScript(special://skin/tools/aster_v2_music.py,shuffle,home)')
        self.assertEqual(root.find(".//control[@id='114']/onright").text,'500')
        self.assertEqual(home.find(".//param[@name='gridup']").get('value'),'115')
        self.assertTrue(any(c.findtext('colordiffuse')=='ff3b3a32' and c.findtext('height')=='160'
            for c in root.findall('.//control')))
        self.assertEqual(root.find(".//control[@id='113']/onright").text,'114')
        self.assertEqual(root.find(".//control[@id='114']/onclick").text,'RunScript(special://skin/tools/aster_v2_music.py,genres,$PARAM[page])')
        source=files['tools/music_data.py'].decode();ast.parse(source)
        self.assertIn("if window.getProperty('AsterMusic.LoadReady') != 'true':\n            return",source)
        self.assertIn("if window.getProperty('AsterMusic.LoadRequest') != request:\n        return",source)
        self.assertIn('xbmcgui.getCurrentWindowId() == PAGES[page]',source)
        self.assertLess(source.index('if not restore_focus'),source.index("window.setProperty('AsterMusic.LoadGeneration', request)"))
        self.assertIn('if handoff(xbmc, xbmcgui, page, identifier_text, source_path)',source)
        self.assertEqual(before,{name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in BEFORE})
        with tempfile.TemporaryDirectory() as directory:
            digest=build(Path(directory)/'overlay','1'*64);self.assertEqual(len(digest),64)
            with self.assertRaises(ValueError):build(Path(directory)/'overlay','1'*64)

    @patch('integration_handoff.platform.node',return_value='AsterTV')
    def test_handoff_emits_only_numeric_ids_or_canonical_server_guid(self,host):
        kodi=Mock();gui=Mock();kodi.getCondVisibility.return_value=True
        self.assertTrue(handoff(kodi,gui,'home','0012'))
        kodi.executebuiltin.assert_called_with('RunScript(script.astermusic.v2lab,album,12)')
        self.assertTrue(handoff(kodi,gui,'songs','13'))
        kodi.executebuiltin.assert_called_with('RunScript(script.astermusic.v2lab,song,13)')
        uri='plugin://plugin.video.jellyfin/?mode=browse&type=playlists&folder='+'A'*32
        self.assertTrue(handoff(kodi,gui,'playlists','',uri))
        kodi.executebuiltin.assert_called_with('RunScript(script.astermusic.v2lab,playlist,'+'a'*32+')')
        for value in ('１','0','12),PlayMedia(x)'):
            kodi.executebuiltin.reset_mock();self.assertTrue(handoff(kodi,gui,'songs',value))
            kodi.executebuiltin.assert_not_called()

    @patch('integration_handoff.platform.node',return_value='AsterTV')
    def test_invalid_remote_playlist_is_refused_but_local_and_artist_routes_remain_native(self,host):
        kodi=Mock();gui=Mock();kodi.getCondVisibility.return_value=True
        self.assertFalse(handoff(kodi,gui,'artists','12'))
        self.assertFalse(handoff(kodi,gui,'playlists','','special://musicplaylists/Mix.m3u'))
        self.assertTrue(handoff(kodi,gui,'playlists','','https://outside.invalid/list'))
        kodi.executebuiltin.assert_not_called();gui.Dialog.return_value.ok.assert_called()
        with patch('integration_handoff.platform.node',return_value='AsterTVProd'):
            self.assertFalse(handoff(kodi,gui,'home','12'))
        kodi.getCondVisibility.return_value=False
        self.assertFalse(handoff(kodi,gui,'home','12'))

    def test_source_return_matches_exact_id_after_reordering_and_consumes_marker(self):
        window=Mock();kodi=Mock()
        window.getProperty.return_value=json.dumps(dict(schema=1,key='album:12',focus=500))
        rows=[dict(id=13),dict(id=9),dict(id=12)]
        self.assertTrue(restore_focus(kodi,window,'home',rows))
        kodi.executebuiltin.assert_called_once_with('Control.SetFocus(500,2,absolute)')
        window.clearProperty.assert_called_once_with(RETURN)
        kodi.executebuiltin.reset_mock()
        self.assertFalse(restore_focus(kodi,window,'home',[dict(id=13)]))
        kodi.executebuiltin.assert_not_called()
        window.getProperty.return_value=json.dumps(dict(schema=1,key='album:12',focus=9999))
        self.assertFalse(restore_focus(kodi,window,'home',rows))

    @patch('integration_handoff.platform.node',return_value='AsterTV')
    def test_header_route_keeps_selected_id_and_header_focus_without_paths(self,host):
        kodi=Mock();gui=Mock();kodi.getCondVisibility.return_value=True
        kodi.getInfoLabel.side_effect=['12','']
        open_route(kodi,gui,'genres','home')
        saved=json.loads(gui.Window.return_value.setProperty.call_args.args[1])
        self.assertEqual(saved,dict(schema=1,key='album:12',focus=114))
        kodi.executebuiltin.assert_called_once_with('RunScript(script.astermusic.v2lab,genres)')
