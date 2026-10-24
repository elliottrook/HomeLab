import importlib.util
import ast
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

    def test_native_tool_sources_parse_without_running_on_the_workstation(self):
        tools=list((HERE/'tools').glob('*.py'))
        self.assertTrue(tools)
        for source in tools:
            with self.subTest(tool=source.name):ast.parse(source.read_text(),filename=str(source))

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
        w=self.window
        with patch.object(self.runtime,'live_grant',return_value=((),3)):w.onClick(201)
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
            self.assertEqual(len(first['files']),36)
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

    def test_shuffle_live_route_requires_the_complete_eligible_grant(self):
        w=self.window;w.open_shuffle=Mock()
        with patch.object(self.runtime,'live_grant',return_value=((1,),20000)):w.onClick(201)
        w.open_shuffle.assert_not_called()
        with patch.object(self.runtime,'live_grant',return_value=((1,3),20000)):w.onClick(201)
        w.open_shuffle.assert_called_once_with(20000)

    def test_shuffle_now_playing_preserves_unknown_artist_truthfully(self):
        w=self.runtime.ShuffleLab();w.allowed=(1,3);w.catalogue=self.window.model.catalogue
        w.session=Mock();w.session.status.return_value=dict(phase='ready',loaded=2,total=2)
        replies={'Player.GetProperties':{'position':1,'speed':1},
                 'Player.GetItem':{'item':{'id':3,'type':'song'}},
                 'AudioLibrary.GetSongDetails':{'songdetails':{}}}
        with patch.object(self.runtime,'rpc',side_effect=lambda m,p:replies[m]):w.refresh()
        self.assertEqual(w.props['Album.Title'],'Untagged')
        self.assertIn('Artist unavailable',w.props['Album.Count'])
        self.assertEqual(w.current_position,1)

    def test_shuffle_queue_paging_does_not_jump_player(self):
        from types import SimpleNamespace
        w=self.runtime.ShuffleLab();w.allowed=tuple(range(1,431));w.session=Mock()
        w.catalogue=SimpleNamespace(songs={i:{'label':str(i)} for i in w.allowed})
        w.onClick(402);self.assertEqual(w.page_offset,200)
        w.onClick(401);self.assertEqual(w.page_offset,0)
        w.current_position=212;w.onClick(403);self.assertEqual(w.page_offset,200)
        w.session.select.assert_not_called();w.session.pause.assert_not_called()

    def test_shuffle_seek_controls_have_explicit_remote_navigation(self):
        window=self.runtime.ShuffleLab();window.focused=400
        action=Mock();action.getId.return_value=1;window.onAction(action)
        self.assertEqual(window.focused,405)
        action.getId.return_value=2;window.onAction(action);self.assertEqual(window.focused,400)
        window.onAction(action);self.assertEqual(window.focused,406)
        action.getId.return_value=3;window.onAction(action);self.assertEqual(window.focused,600)

    def test_floating_controls_fit_cover_and_keep_readable_focus_caption(self):
        window=self.runtime.ShuffleLab();window.allowed=(1,)
        controls={identity:Mock() for identity in (400,401,402,403,404,405,406,8400,8401,8402,8403,8404,8405,8406,9400,9401,9402,9403,9404,9405,9406,10400,10401,10402,10403,10404,10405,10406)}
        window.getControl=lambda identity:controls[identity]
        window.configure_controls(shuffle=True)
        for identity in (400,401,402,403,404,405,406):
            left,top=controls[identity].setPosition.call_args.args
            width=controls[identity].setWidth.call_args.args[0]
            self.assertGreaterEqual(left,170);self.assertLessEqual(left+width,700)
            self.assertEqual(top,930);self.assertGreaterEqual(width,44)
        window.onFocus(405);self.assertEqual(window.props['Album.ControlHint'],'Back 10 seconds')
        window.focus_control(406)
        self.assertEqual(window.focused,406)
        self.assertEqual(window.props['Album.ControlHint'],'Forward 10 seconds')

    def test_icon_controls_have_no_pill_and_artwork_is_square_aspect_kept(self):
        root=ET.parse(HERE/'script.astermusic.v2lab/resources/skins/Default/1080i/AlbumLab.xml')
        controls=root.findall('.//control')
        for identity in range(400,407):
            button=next(c for c in controls if c.get('id')==str(identity))
            self.assertFalse(button.findtext('texturefocus'));self.assertFalse(button.findtext('texturenofocus'))
            self.assertEqual(button.findtext('textcolor'),'00000000')
            self.assertTrue(button.findtext('label'))  # Native label retained for accessibility.
        art=next(c for c in controls if c.findtext('texture')=='$INFO[Window.Property(Album.Art)]')
        self.assertEqual(art.findtext('width'),'530');self.assertEqual(art.findtext('height'),'530')
        self.assertEqual(art.findtext('aspectratio'),'keep')
        title=next(c for c in controls if c.findtext('label')=='$INFO[Window.Property(Album.Title)]')
        self.assertEqual(title.get('type'),'label');self.assertEqual(title.findtext('width'),'530')
        self.assertEqual(title.findtext('scroll'),'true')
        for source in (HERE/'script.astermusic.v2lab/resources/controls').glob('*.svg'):
            icon=ET.parse(source).getroot();self.assertEqual(icon.get('viewBox'),'0 0 64 64')
            self.assertTrue(source.with_suffix('.png').is_file())

    def test_floating_pause_and_seek_clicks_dispatch_to_existing_owned_session(self):
        window=self.runtime.ShuffleLab();window.control=Mock();window.paused=True
        window.onClick(400);window.control.assert_called_with('pause',True)
        window.onClick(405);window.control.assert_called_with('seek',-10)
        window.onClick(406);window.control.assert_called_with('seek',10)

    def test_shuffle_unsupported_seek_explains_without_closing_player(self):
        window=self.runtime.ShuffleLab();window.session=Mock()
        window.session.status.return_value=dict(phase='ready',loaded=1,total=1)
        window.control_worker=Mock();window.control_worker.is_alive.return_value=False
        window.control_errors=[self.runtime.TrialUnavailable('seek-unavailable')]
        window.next_player_update=float('inf')
        window.refresh()
        self.assertFalse(window.finished)
        self.gui.Dialog.return_value.ok.assert_called()

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

    def test_shuffle_close_cancels_and_joins_control_before_session_cleanup(self):
        window=self.runtime.ShuffleLab();events=[]
        window.session=Mock();window.control_worker=Mock()
        window.session.engine.cancel.set.side_effect=lambda:events.append('cancel')
        window.control_worker.join.side_effect=lambda:events.append('join-control')
        window.session.close.side_effect=lambda:events.append('close-session')
        window.close();window.close()
        self.assertEqual(events,['cancel','join-control','close-session'])
        self.assertTrue(window.finished);self.assertTrue(window.closed)

    def test_shuffle_close_preserves_recovery_flag_on_uncertain_queue(self):
        window=self.runtime.ShuffleLab();window.session=Mock()
        window.session.close.side_effect=ValueError('foreign-queue')
        window.close()
        self.gui.Window.return_value.setProperty.assert_called_with('AsterV2Lab.TrialRecovery','required')
        self.assertTrue(window.closed)

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

    def test_expired_capability_is_rechecked_before_native_queue_write(self):
        window=self.runtime.AlbumLab();window.allowed=(1,)
        def construct(transport,*args,**kwargs):
            transport('Playlist.Add',{'playlistid':0,'item':[{'songid':1}]})
            raise AssertionError('expired grant reached native writer')
        with patch.object(self.runtime,'live_grant',side_effect=[((1,),3),((),3)]),\
             patch.object(self.runtime,'ExpandedTrial',side_effect=construct):
            window.live('append',(1,))
        self.assertIn('trial-capability-expired',window.props['Album.Status'])
        self.xbmc.executeJSONRPC.assert_not_called()


if __name__=='__main__':unittest.main()
