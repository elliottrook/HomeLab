import importlib.util,json,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import xml.etree.ElementTree as ET
from review2_ui import quiet_buttons,search_focus,header,osd,keyboard,select_dialog
from tools import deploy_review2 as deploy
HERE=Path(__file__).parent

class ReviewLayouts(unittest.TestCase):
    def test_header_search_first_equal_spacing(self):
        from build_global_search import build
        from feedback_refinements import media_header
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'search';build(path,True,True,'aster-global-search-ui12')
            root=ET.fromstring(header(media_header((path/'overlay/Home.xml').read_bytes())))
        for index,identity in enumerate((135,130,131,132,133,134,136)):
            node=root.find(f'.//control[@id="{identity}"]')
            self.assertEqual(node.findtext('left'),str(375+index*192))
            self.assertEqual(node.findtext('width'),'180');self.assertEqual(node.findtext('aligny'),'center')
    def test_music_clock_above_full_art_width_scrub(self):
        root=ET.parse(HERE/'script.astermusic.v2lab/resources/skins/Default/1080i/AlbumLab.xml')
        progress=root.find('.//control[@id="610"]');hit=root.find('.//control[@id="611"]')
        self.assertEqual(progress.findtext('width'),'530');self.assertEqual(hit.findtext('width'),'530')
        clocks=[c for c in root.findall('.//control') if c.findtext('label')=='$INFO[Window.Property(Album.Clock)]']
        self.assertEqual(len(clocks),2)
        for c in clocks:self.assertLessEqual(int(c.findtext('top'))+int(c.findtext('height')),int(progress.findtext('top')))
        self.assertTrue(any(c.findtext('textcolor')=='ff005c46' and '!Player.Paused' in c.findtext('visible') for c in clocks))
    def test_season_selector_is_anchored_not_native_dialog(self):
        root=ET.parse(HERE/'series_preview/resources/skins/Default/1080i/SeriesPreview.xml')
        self.assertEqual(root.findtext('.//control[@id="300"]/onup'),'201')
        self.assertEqual(root.findtext('.//control[@id="301"]/left'),'905')
        source=(HERE/'series_preview/default.py').read_text()
        self.assertNotIn("self.dialog('select','Choose season'",source)
        self.assertIn("control==300 and key==3",source)
    def test_search_focus_ring_and_marker_follow_actual_focus(self):
        root=ET.fromstring(search_focus((HERE/'search_native/overlay/custom_1127_search.xml').read_bytes()))
        for i in (20,30):
            images=root.findall(f'.//control[@id="{i}"]/focusedlayout/control[@type="image"]')
            self.assertGreaterEqual(len(images),2)
            self.assertTrue(all(c.findtext('visible')==f'Control.HasFocus({i})' for c in images))
    def test_search_direct_link_does_not_require_interstitial(self):
        source=(HERE/'search_native/default.py').read_text()
        self.assertIn("active_detail=hit;command='open'",source)
        self.assertIn("(source_visible() or xbmc.getCondVisibility('Window.IsVisible(11128)'))",source)
    def test_keyboard_retains_all_native_ids_and_uses_black_panel(self):
        data=(HERE.parent/'skin.asterhome/1080i/DialogKeyboard.xml').read_bytes()
        old=ET.fromstring(data);new=ET.fromstring(keyboard(data))
        self.assertEqual([n.get('id') for n in old.iter('control') if n.get('id')],
                         [n.get('id') for n in new.iter('control') if n.get('id')])
        self.assertIn('df000000',ET.tostring(new).decode());self.assertNotIn('limestone',ET.tostring(new).decode())
        self.assertFalse(any(c.findtext('width')=='1920' for c in new.findall('./controls/control[@type="image"]')))
    def test_generic_select_is_compact_and_retains_native_ids(self):
        root=ET.fromstring(select_dialog((HERE.parent/'skin.asterhome/1080i/DialogSelect.xml').read_bytes()))
        for i in (1,3,5,60):self.assertIsNotNone(root.find(f'.//control[@id="{i}"]'))
        group=root.find('./controls/control[@type="group"]')
        self.assertEqual(group.findtext('width'),'620');self.assertEqual(group.findtext('left'),'1100')
    def test_stone_only_removed_from_buttons(self):
        data=b'<window><controls><control type="image"><texture>stone-scene.png</texture></control><control type="button"><texturenofocus>ui-limestone-panel.png</texturenofocus></control></controls></window>'
        text=quiet_buttons(data).decode();self.assertIn('stone-scene.png',text);self.assertNotIn('limestone',text)
    def test_osd_replaces_only_three_settings_routes(self):
        data=(HERE.parent/'skin.asterhome/1080i/VideoOSD.xml').read_bytes();old=ET.fromstring(data);new=ET.fromstring(osd(data))
        for i,k in ((7100,'audio'),(7101,'subtitles'),(7102,'quality')):
            self.assertEqual(new.findtext(f'.//control[@id="{i}"]/onclick'),'RunScript(special://skin/tools/osd_choices.py,'+k+')')
        for i in (600,601,602,603,605,606,607):self.assertEqual(ET.tostring(old.find(f'.//control[@id="{i}"]')),ET.tostring(new.find(f'.//control[@id="{i}"]')))

class OsdChoices(unittest.TestCase):
    def setUp(self):
        self.xbmc=Mock();self.gui=Mock();self.menu=Mock();self.menu.choose.return_value=-1
        spec=importlib.util.spec_from_file_location('review_osd_test',HERE/'osd_choices.py')
        self.module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,dict(xbmc=self.xbmc,xbmcgui=self.gui,compact_menu=self.menu)):spec.loader.exec_module(self.module)
        self.xbmc.Player.return_value.isPlayingVideo.return_value=True
        self.xbmc.Player.return_value.getPlayingFile.return_value='synthetic://owned'
        self.calls=[];self.active=[dict(playerid=1,type='video',playertype='internal')]
        self.state=dict(subtitles=[dict(index=3,language='eng',name='English')],currentsubtitle=dict(index=3),subtitleenabled=False)
        def rpc(method,params):
            self.calls.append((method,params))
            if method=='Player.GetActivePlayers':return self.active
            if method=='Player.GetProperties':return self.state
            return 'OK'
        self.module.rpc=rpc
        p=patch.object(self.module.os,'uname',return_value=SimpleNamespace(nodename='AsterTV'));p.start();self.addCleanup(p.stop)
    def test_subtitle_menu_lists_toggle_first_and_enables_exact_stream(self):
        self.menu.choose.return_value=1;self.module.main('subtitles')
        self.assertTrue(self.menu.choose.call_args.args[1][0].startswith('Subtitles: Off'))
        self.assertEqual(self.calls[-1],('Player.SetSubtitle',dict(playerid=1,subtitle=3,enable=True)))
    def test_subtitle_toggle_off(self):
        self.state['subtitleenabled']=True;self.menu.choose.return_value=0;self.module.main('subtitles')
        self.assertEqual(self.calls[-1],('Player.SetSubtitle',dict(playerid=1,subtitle='off')))
    def test_cancel_and_player_replacement_make_no_write(self):
        self.module.main('subtitles');self.assertFalse(any(m.startswith('Player.Set') for m,p in self.calls))
        def replace(*args,**kwargs):self.xbmc.Player.return_value.getPlayingFile.return_value='synthetic://foreign';return 1
        self.menu.choose.side_effect=replace;self.module.main('subtitles')
        self.assertFalse(any(m.startswith('Player.Set') for m,p in self.calls))
    def test_audio_switch_uses_stream_id_not_row(self):
        self.state=dict(audiostreams=[dict(index=5,language='eng')],currentaudiostream=dict(index=0))
        self.menu.choose.return_value=0;self.module.main('audio')
        self.assertEqual(self.calls[-1],('Player.SetAudioStream',dict(playerid=1,stream=5)))
    def test_quality_never_changes_display_or_transcode(self):
        self.state=dict(currentvideostream=dict(width=3840,height=2160,codec='hevc'))
        self.menu.choose.return_value=0;self.module.main('quality')
        self.assertIn('3840 × 2160',self.menu.choose.call_args.args[1][0])
        self.assertFalse(any(m.startswith('Player.Set') for m,p in self.calls))

class ReviewDeploy(unittest.TestCase):
    def test_rejects_profiles_side_rail_and_production_helpers(self):
        for name in ('../x','/storage/x','.kodi/userdata/guisettings.xml','.kodi/addons/skin.asterhome/1080i/IncludesHub.xml',
                     '.kodi/addons/plugin.video.jellyfin/player.py','.aster-staging/arbitrary/file.py'):
            self.assertFalse(deploy.allowed(name),name)
        self.assertTrue(deploy.allowed('.kodi/addons/skin.asterhome/tools/compact_menu.py'))
    def test_install_verify_rollback_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            storage=Path(directory).resolve();stage=storage/'.aster-staging/aster-review2';stage.mkdir(parents=True)
            rows=[]
            for i in range(51):
                name=f'.kodi/addons/script.astermusic.v2lab/test_{i}.py';old=b'value=1\n';new=b'value=2\n'
                target=storage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(old)
                source=stage/'payload'/name;source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(new)
                rows.append(dict(path=name,sha256=deploy.sha(source),before_sha256=deploy.sha(target)))
            (stage/'manifest.json').write_text(json.dumps(dict(kind='hp-review2',name='aster-review2',files=rows)))
            digest=deploy.sha(stage/'manifest.json');proof='postcheck-'+str(time.time_ns())+'.json'
            path=storage/'.aster-checkpoints/aster-music-progressive-20261024'/proof;path.parent.mkdir(parents=True)
            path.write_text(json.dumps(dict(av_language_settings_verified=68,approved_search_details_files_verified=6,
                **{k:True for k in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off')})))
            with patch.object(deploy.subprocess,'run',return_value=SimpleNamespace(stdout='0')):
                self.assertTrue(deploy.run('install',digest,proof,storage)['installed'])
                self.assertTrue(deploy.run('verify',digest,proof,storage)['verified'])
                self.assertTrue(deploy.run('rollback',digest,proof,storage)['rolled_back'])
            for row in rows:self.assertEqual(deploy.sha(storage/row['path']),row['before_sha256'])
