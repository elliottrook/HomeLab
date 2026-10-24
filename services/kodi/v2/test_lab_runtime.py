import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
import xml.etree.ElementTree as ET

from build_lab import build
from lab_model import LabModel
from music_catalogue import read_catalogue
from test_music_catalogue import FakeLibrary

HERE=Path(__file__).parent


class FakeWindow:
    def __init__(self,*args,**kwargs):self.props={};self.focused=500;self.closed=False
    def setProperty(self,k,v):self.props[k]=v
    def getProperty(self,k):return self.props.get(k,'')
    def setFocusId(self,i):self.focused=i
    def getFocusId(self):return self.focused
    def getControl(self,i):return Mock()
    def close(self):self.closed=True


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.xbmc=Mock();self.gui=Mock();self.gui.WindowXML=FakeWindow
        with patch.dict(sys.modules,{'xbmc':self.xbmc,'xbmcgui':self.gui}):
            spec=importlib.util.spec_from_file_location('aster_v2_lab_runtime',HERE/'script.astermusic.v2lab/default.py')
            self.runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.runtime)
        self.xbmc.executeJSONRPC.return_value=json.dumps({'result':{}})
        self.window=self.runtime.MusicLab()
        self.window.model=LabModel(read_catalogue(FakeLibrary()))

    def action(self,identity):
        action=Mock();action.getId.return_value=identity;self.window.onAction(action)

    def test_rpc_refuses_all_mutating_methods(self):
        for method in ('Player.Open','Playlist.Clear','AudioLibrary.SetSongDetails','GUI.ActivateWindow'):
            with self.assertRaises(ValueError):self.runtime.rpc(method,{})
        self.xbmc.executeJSONRPC.assert_not_called()

    def test_arrow_column_retained_after_deferred_focus_callback(self):
        w=self.window;w.model.index=w.model.column=3;w.focused=503
        self.action(4);self.assertEqual(w.focused,506)
        w.onFocus(506)  # Kodi callbacks are queued, not synchronous.
        self.action(3);self.assertEqual(w.focused,503)

    def test_rail_focus_and_back_restore_tile(self):
        self.action(1)
        self.assertEqual(self.window.focused,9007)
        self.assertTrue(self.window.rail)
        self.action(92)
        self.assertEqual(self.window.focused,500)
        self.assertFalse(self.window.rail)

    def test_click_opens_real_genre_and_back_restores_position(self):
        w=self.window;w.onClick(502)
        self.assertEqual(w.model.category,'Rock & Alternative')
        self.action(92)
        self.assertEqual(w.model.mode,'genres');self.assertEqual(w.focused,502)
        self.action(92);self.assertTrue(w.closed)

    def test_shuffle_and_song_select_only_display_explanations(self):
        w=self.window;w.onClick(201)
        self.gui.Dialog.return_value.ok.assert_called()
        w.onClick(502);w.onClick(102);w.onClick(500)
        methods=[json.loads(c.args[0])['method'] for c in self.xbmc.executeJSONRPC.call_args_list]
        self.assertTrue(all(m in self.runtime.READS for m in methods))
        self.assertNotIn('Player.Open',methods)

    def test_cancelled_or_failed_refresh_keeps_previous_view(self):
        w=self.window;before=w.model.catalogue
        with patch.object(self.runtime,'load_catalogue',return_value=(None,'Refresh cancelled')):w.onClick(302)
        self.assertIs(w.model.catalogue,before)
        self.assertIn('previous view retained',w.props['Lab.Status'])

    def test_artwork_lookups_are_lazy_cached_and_never_fetch_paths(self):
        w=self.window;w.onClick(502)
        before=self.xbmc.executeJSONRPC.call_count
        w.hero();w.hero()
        self.assertEqual(self.xbmc.executeJSONRPC.call_count,before)
        request=json.loads(self.xbmc.executeJSONRPC.call_args.args[0])
        self.assertEqual(request['params']['properties'],['thumbnail'])

    def test_unique_controls_self_navigation_and_existing_assets(self):
        root=ET.parse(HERE/'script.astermusic.v2lab/resources/skins/Default/1080i/MusicLab.xml')
        ids=[n.get('id') for n in root.findall('.//control') if n.get('id')]
        self.assertEqual(len(ids),len(set(ids)))
        for control in root.findall('.//control[@type="button"]'):
            for direction in ('onleft','onright','onup','ondown'):
                self.assertEqual(control.findtext(direction),control.get('id'))
        for node in root.findall('.//texture'):
            text=node.text or ''
            if text.startswith('special://home/addons/skin.asterhome/media/'):
                self.assertTrue((HERE.parent/'skin.asterhome/media'/text.rsplit('/',1)[-1]).is_file())

    def test_build_is_deterministic_and_v1_source_is_not_part_of_bundle(self):
        with tempfile.TemporaryDirectory() as one,tempfile.TemporaryDirectory() as two:
            first=build(one);second=build(two)
            self.assertEqual(first['sha256'],second['sha256'])
            self.assertEqual(len(first['files']),7)
            self.assertTrue(all(r['path'].startswith('script.astermusic.v2lab/') for r in first['files']))


if __name__=='__main__':unittest.main()
