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
        self.assertEqual(root.find('defaultcontrol').get('always'),'false')
        self.assertEqual(len(ids),len(set(ids)))
        for control in root.findall('.//control[@type="button"]'):
            for direction in ('onleft','onright','onup','ondown'):
                self.assertEqual(control.findtext(direction),control.get('id'))
        for node in root.findall('.//texture'):
            text=node.text or ''
            if text.startswith('special://home/addons/skin.asterhome/media/'):
                self.assertTrue((HERE.parent/'skin.asterhome/media'/text.rsplit('/',1)[-1]).is_file())

    def test_clock_is_centred_in_unchanged_pill_and_uses_24_hour_time(self):
        root=ET.parse(HERE/'script.astermusic.v2lab/resources/skins/Default/1080i/MusicLab.xml')
        clock=next(c for c in root.findall('.//control[@type="label"]')
                   if c.findtext('label')=='$INFO[System.Time(hh:mm)]')
        self.assertEqual(clock.findtext('align'),'center')
        self.assertEqual(clock.findtext('aligny'),'center')
        bounds=tuple(clock.findtext(k) for k in ('left','top','width','height'))
        self.assertEqual(bounds,('1715','31','145','48'))
        self.assertTrue(any(tuple(c.findtext(k) for k in ('left','top','width','height'))==bounds
                            for c in root.findall('.//control[@type="image"]')))

    def test_build_is_deterministic_and_v1_source_is_not_part_of_bundle(self):
        with tempfile.TemporaryDirectory() as one,tempfile.TemporaryDirectory() as two:
            first=build(one);second=build(two)
            self.assertEqual(first['sha256'],second['sha256'])
            self.assertEqual(len(first['files']),13)
            self.assertTrue(all(r['path'].startswith('script.astermusic.v2lab/') for r in first['files']))
            self.assertTrue(any(r['path'].endswith('/music_queue.py') for r in first['files']))
            self.assertTrue(any(r['path'].endswith('/music_album.py') for r in first['files']))

    def test_album_queue_actions_are_read_only_previews(self):
        from music_album import order_album
        from music_queue import QueueSnapshot
        window=self.runtime.AlbumLab()
        window.selection=order_album(7,[dict(songid=1,albumid=7,disc=1,track=1,
                                            duration=180,label='One')],[1])
        with patch.object(self.runtime,'read_queue',return_value=QueueSnapshot((),None)):
            for control in (401,402,403):window.onClick(control)
        self.assertEqual(self.gui.Dialog.return_value.ok.call_count,3)
        self.xbmc.executeJSONRPC.assert_not_called()

    def test_album_back_and_button_focus_contract(self):
        window=self.runtime.AlbumLab();window.focused=401
        action=Mock();action.getId.return_value=2;window.onAction(action)
        self.assertEqual(window.focused,402)
        action.getId.return_value=3;window.onAction(action)
        self.assertEqual(window.focused,600)
        action.getId.return_value=92;window.onAction(action)
        self.assertTrue(window.closed)

    def test_album_layout_fonts_clock_and_control_navigation_are_defined(self):
        root=ET.parse(HERE/'script.astermusic.v2lab/resources/skins/Default/1080i/AlbumLab.xml')
        fonts={n.text for n in ET.parse(HERE.parent/'skin.asterhome/1080i/Font.xml').findall('.//name')}
        self.assertTrue(all(n.text in fonts for n in root.findall('.//font')))
        controls=root.findall('.//control')
        ids=[c.get('id') for c in controls if c.get('id')]
        self.assertEqual(len(ids),len(set(ids)))
        clock=next(c for c in controls if c.findtext('label')=='$INFO[System.Time(hh:mm)]')
        self.assertEqual(clock.findtext('align'),'center')
        self.assertEqual(clock.findtext('aligny'),'center')
        for c in controls:
            if c.get('id') in ('401','402','403','600'):
                for direction in ('onleft','onright','onup','ondown'):
                    self.assertEqual(c.findtext(direction),c.get('id'))

    def test_album_unknown_disc_label_is_truthful_and_queue_failure_is_safe(self):
        from music_album import order_album
        from queue_reader import QueueUnavailable
        window=self.runtime.AlbumLab();window.title='Album';window.artwork=''
        window.selection=order_album(7,[dict(songid=1,albumid=7,disc=0,track=1,
                                            duration=180,label='One')],[1])
        window.onInit()
        self.assertIn('disc numbers unavailable',window.props['Album.Count'])
        with patch.object(self.runtime,'read_queue',side_effect=QueueUnavailable('unsupported-queue-item')):
            window.onClick(403)
        self.assertIn('unchanged',self.gui.Dialog.return_value.ok.call_args.args[1])
        self.xbmc.executeJSONRPC.assert_not_called()

    def test_album_cleanup_is_idempotent_when_back_and_finally_both_close(self):
        window=self.runtime.AlbumLab();window.trial=Mock()
        window.close();window.close()
        window.trial.close.assert_called_once()
        self.assertTrue(window.finished)

    def test_popup_cancel_back_never_closes_underlying_trial(self):
        window=self.runtime.AlbumLab();window.trial=Mock()
        action=Mock();action.getId.return_value=92
        self.gui.Dialog.return_value.yesno.side_effect=lambda *args:window.onAction(action) or False
        self.assertFalse(window.dialog('yesno','Replace','Confirm'))
        window.onAction(action)  # Also consume the native modal's queued Back.
        self.assertFalse(window.finished)
        window.trial.close.assert_not_called()

    def test_positive_confirmation_does_not_block_immediate_player_exit(self):
        window=self.runtime.AlbumLab();window.trial=Mock()
        self.gui.Dialog.return_value.yesno.return_value=True
        self.assertTrue(window.dialog('yesno','Play','Confirm'))
        action=Mock();action.getId.return_value=92;window.onAction(action)
        window.trial.close.assert_called_once()

    def test_late_select_on_closing_album_never_opens_another_dialog(self):
        window=self.runtime.AlbumLab();window.finished=True
        window.onClick(600);window.onClick(400)
        self.gui.Dialog.assert_not_called()
        self.xbmc.executeJSONRPC.assert_not_called()


if __name__=='__main__':unittest.main()
