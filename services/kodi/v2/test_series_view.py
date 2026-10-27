import ast,unittest,tempfile,importlib.util,sys
from unittest.mock import Mock,patch
from pathlib import Path
import xml.etree.ElementTree as ET
from series_model import build_series
from series_catalogue import merge_page,parse_catalogue,parse_season
from series_view import SeriesSelection,episode_metadata
from test_series_model import episode
from build_series_preview import build

HERE=Path(__file__).parent
class SeriesViewTests(unittest.TestCase):
    def test_exact_episode_focus_is_remembered_per_season(self):
        page=build_series(12,[episode(),episode(2,1,2),episode(3,2,1)],expected_total=3)
        view=SeriesSelection(page);view.select(1)
        self.assertTrue(view.change_season(1));self.assertEqual(view.episode.episode_id,3)
        self.assertTrue(view.change_season(0));self.assertEqual(view.episode.episode_id,2)
        self.assertFalse(view.change_season(-1));self.assertEqual(view.episode.episode_id,2)

    def test_resume_identity_sets_initial_season_and_row(self):
        page=build_series(12,[episode(),episode(2,2,1)],expected_total=2)
        view=SeriesSelection(page,2);self.assertEqual((view.season,view.index),(1,0))

    def test_native_next_tracks_exact_episode_across_seasons_without_guessing(self):
        page=build_series(12,[episode(),episode(2,1,2),episode(3,2,1)],expected_total=3)
        view=SeriesSelection(page,2)
        self.assertTrue(view.follow_episode(3));self.assertEqual((view.season,view.index),(1,0))
        self.assertTrue(view.change_season(0));self.assertEqual(view.episode.episode_id,2)
        for value in (999,True,'3',None):
            self.assertFalse(view.follow_episode(value));self.assertEqual(view.episode.episode_id,2)

    def test_empty_and_unknown_values_do_not_invent_content(self):
        view=SeriesSelection(build_series(12,[],expected_total=0))
        self.assertIsNone(view.episode);self.assertFalse(view.change_season(0));view.select(0)
        row=build_series(12,[episode(1,None,None)],expected_total=1).seasons[0].episodes[0]
        self.assertEqual(episode_metadata(row),'Episode number unavailable · Duration unavailable · Air date unavailable')

    def test_native_layout_has_stable_rows_and_quiet_floating_pills(self):
        root=ET.parse(HERE/'series_preview/resources/skins/Default/1080i/SeriesPreview.xml')
        rows=root.find('.//control[@id="300"]')
        self.assertEqual(rows.find('itemlayout').attrib,rows.find('focusedlayout').attrib)
        self.assertEqual(rows.findtext('width'),'920')
        ids=[n.get('id') for n in root.findall('.//control') if n.get('id')]
        self.assertEqual(len(ids),len(set(ids)))
        for layout in (rows.find('itemlayout'),rows.find('focusedlayout')):
            for control in layout.findall('control'):
                self.assertLessEqual(int(control.findtext('left'))+int(control.findtext('width')),920)
                self.assertLessEqual(int(control.findtext('top'))+int(control.findtext('height')),210)
        self.assertEqual(root.findtext('defaultcontrol'),'202')
        home=ET.parse(HERE.parent/'skin.asterhome/1080i/Home.xml')
        home_ring_colours=[c.findtext('colordiffuse') for c in home.findall('.//focusedlayout/control')
                           if (c.findtext('texture') or '').endswith('/ui-compact-card-ring.png')][:2]
        for layout in (rows.find('itemlayout'),rows.find('focusedlayout')):
            plates=[c for c in layout.findall('control') if (c.findtext('texture') or '').endswith('/ui-panel.png')]
            self.assertEqual(len(plates),3)
            self.assertEqual(int(layout.get('height'))-int(plates[1].findtext('height')),12)
            self.assertEqual(plates[1].find('texture').get('border'),'24')
            rings=[c for c in layout.findall('control') if (c.findtext('texture') or '').endswith('/ui-compact-card-ring.png')]
            self.assertEqual([c.find('texture').get('colordiffuse') for c in rings],['asterIvory','asterGreen'])
            self.assertEqual([c.find('texture').get('colordiffuse') for c in rings],home_ring_colours)
            self.assertEqual([(c.findtext('left'),c.findtext('top'),c.findtext('width'),c.findtext('height')) for c in rings],
                             [('0','0','900','198'),('2','2','896','194')])
            for ring in rings:
                self.assertEqual(ring.find('texture').get('border'),'20')
                self.assertEqual(ring.findtext('visible'),'String.IsEqual(ListItem.Property(Selected),true)')
            self.assertFalse(any(c.findtext('width')=='4' for c in layout.findall('control')))
            titles=[c for c in layout.findall('control') if c.findtext('label')=='$INFO[ListItem.Label]']
            self.assertEqual(len(titles),2)
            selected=next(c for c in titles if c.findtext('textcolor')=='ff005c46')
            self.assertEqual(selected.findtext('visible'),'String.IsEqual(ListItem.Property(Selected),true)')

    def test_preview_dispatch_has_no_playback_or_server_writes(self):
        source=(HERE/'series_preview/default.py').read_text();ast.parse(source)
        self.assertNotIn('PlayMedia(',source)
        self.assertNotIn('urllib',source);self.assertNotIn('requests.',source)
        self.assertNotIn('assert ',source)

    def test_stills_and_fallback_are_centred_in_pills_with_progress_clear(self):
        root=ET.parse(HERE/'series_preview/resources/skins/Default/1080i/SeriesPreview.xml')
        for layout in root.find('.//control[@id="300"]'):
            if layout.tag not in ('itemlayout','focusedlayout'):continue
            media=[c for c in layout.findall('control') if c.findtext('left')=='12' and c.findtext('height')=='118']
            self.assertEqual(len(media),3)
            for control in media:
                self.assertEqual(int(control.findtext('top'))*2+int(control.findtext('height')),198)
                self.assertEqual(control.findtext('width'),'198')
            bar=layout.find('control[@type="progress"]')
            self.assertGreater(int(bar.findtext('top')),158)
            status=next(c for c in layout.findall('control') if c.findtext('label')=='$INFO[ListItem.Property(State)]')
            self.assertGreater(int(status.findtext('top')),int(bar.findtext('top'))+3)
            self.assertLessEqual(int(status.findtext('top'))+int(status.findtext('height')),198)
            for label,top in (('$INFO[ListItem.Label]','0'),('$INFO[ListItem.Property(Metadata)]','40'),
                              ('$INFO[ListItem.Property(Synopsis)]','78')):
                for control in (c for c in layout.findall('control') if c.findtext('label')==label):
                    self.assertEqual(control.findtext('top'),top)

    def test_episode_pills_float_directly_on_hero_without_shared_panel(self):
        root=ET.parse(HERE/'series_preview/resources/skins/Default/1080i/SeriesPreview.xml')
        for image in root.findall('./controls/control[@type="image"]'):
            if (image.findtext('texture') or '').endswith('/ui-panel.png'):
                self.assertLessEqual(int(image.findtext('width')),200)  # Clock only.
        for identity in ('201',):
            heading=root.find('.//control[@id="'+identity+'"]')
            self.assertEqual(heading.findtext('textcolor'),'fff3eee5')
            self.assertEqual(heading.findtext('shadowcolor'),'ff202b25')

    def test_preview_build_is_deterministic_and_refuses_overwrite(self):
        import json,hashlib
        with tempfile.TemporaryDirectory() as parent:
            first=Path(parent)/'one';second=Path(parent)/'two'
            self.assertEqual(build(first),build(second))
            manifest=json.loads((first/'manifest.json').read_text())
            self.assertEqual(len(manifest['files']),8)
            for row in manifest['files']:
                data=(first/row['path']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
                self.assertEqual(len(data),row['bytes'])
            with self.assertRaises(ValueError):build(first)

    def test_native_async_initialization_cannot_read_controls_early(self):
        class Window:
            def __init__(self,*a):self.closed=0
            def close(self):self.closed+=1
        gui=Mock();gui.WindowXML=Window
        with patch.dict(sys.modules,{'xbmc':Mock(),'xbmcgui':gui}):
            spec=importlib.util.spec_from_file_location('aster_series_preview_runtime',HERE/'series_preview/default.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            window=module.SeriesPreview();window.getControl=Mock(side_effect=AssertionError('early-control'))
            window.publish();window.getControl.assert_not_called()
            self.assertFalse(window.ready);self.assertIsNone(window.identity)
            window.close();window.close();self.assertTrue(window.finished);self.assertEqual(window.closed,1)

    def test_fullscreen_return_retains_allocated_window_and_rebuilds_header(self):
        from types import SimpleNamespace
        gui=Mock();gui.WindowXML=type('Window',(),{'__init__':lambda self,*a:None})
        gui.getCurrentWindowId.return_value=10000
        with patch.dict(sys.modules,{'xbmc':Mock(),'xbmcgui':gui}):
            spec=importlib.util.spec_from_file_location('aster_series_return_runtime',HERE/'series_preview/default.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            window=module.SeriesPreview();window.ready=True;window.identity=13001
            page=build_series(12,[episode()],expected_total=1)
            window.snapshot=SimpleNamespace(page=page,title='Series',synopsis='Synopsis',fanart='',genres=(),year=None,rating=None,certificate='')
            original=window.selection=SeriesSelection(page)
            window.populate=Mock();window.setProperty=Mock();window.setFocusId=Mock();window.publish=Mock()
            window.onInit()
            self.assertEqual(window.identity,13001);self.assertIs(window.selection,original)
            window.setProperty.assert_any_call('Series.Title','Series')
            gui.Window.return_value.setProperty.assert_called_with('AsterSeries.PreviewWindow','13001')

    def test_closing_hidden_series_cannot_indirectly_stop_external_video(self):
        gui=Mock();gui.WindowXML=type('Window',(),{'__init__':lambda self,*a:None})
        with patch.dict(sys.modules,{'xbmc':Mock(),'xbmcgui':gui}):
            spec=importlib.util.spec_from_file_location('aster_series_conflict_runtime',HERE/'series_preview/default.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            for phase in ('conflict','recovery'):
                window=module.SeriesPreview();window.session=Mock(phase=phase,can_close=True)
                window.finish_close=Mock()
                with patch.object(module,'rpc',return_value=[dict(playerid=1,type='video')]):window.close()
                window.finish_close.assert_not_called();self.assertTrue(window.close_requested)
                with patch.object(module,'rpc',return_value=[]):window.close()
                window.finish_close.assert_called_once()

    def test_catalogue_episode_uses_two_step_season_request_not_player(self):
        from types import SimpleNamespace
        gui=Mock();gui.WindowXML=type('Window',(),{'__init__':lambda self,*a:None})
        with patch.dict(sys.modules,{'xbmc':Mock(),'xbmcgui':gui}):
            spec=importlib.util.spec_from_file_location('aster_series_request_runtime',HERE/'series_preview/default.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            raw={'schema':1,'candidate_id':'seerr:tv:456','title':'Series','seasons':[
                {'number':2,'name':'Season 2','episode_count':1,'state':'unknown',
                 'request_id':None,'request_state':'none','requestable':True}]}
            catalogue=parse_catalogue(raw)
            detail=parse_season({'schema':1,'candidate_id':'seerr:tv:456','title':'Series',
                'season':raw['seasons'][0],'episodes':[{'number':1,'title':'Missing',
                'overview':'','air_date':'2026-01-01','still':''}]},catalogue,2)
            page=merge_page(build_series(12,[episode()],expected_total=1),catalogue,[detail])
            row=page.seasons[1].episodes[0]
            window=module.SeriesPreview();window.catalogue=catalogue
            window.setProperty=Mock();window.session=Mock();window.season_writer=Mock()
            window.season_writer.submit.return_value={'state':'pending'}
            window.request_missing(row)
            window.season_writer.submit.assert_not_called()
            window.request_missing(row)
            window.season_writer.submit.assert_called_once()
            window.session.start.assert_not_called()

    def test_catalogue_art_is_deferred_until_after_navigation_is_ready(self):
        from types import SimpleNamespace
        gui=Mock();gui.WindowXML=type('Window',(),{'__init__':lambda self,*a:None})
        with patch.dict(sys.modules,{'xbmc':Mock(),'xbmcgui':gui}):
            spec=importlib.util.spec_from_file_location('aster_series_async_art_runtime',HERE/'series_preview/default.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            raw={'schema':1,'candidate_id':'seerr:tv:456','title':'Series','seasons':[
                {'number':2,'name':'Season 2','episode_count':1,'state':'unknown',
                 'request_id':None,'request_state':'none','requestable':True}]}
            catalogue=parse_catalogue(raw)
            detail=parse_season({'schema':1,'candidate_id':'seerr:tv:456','title':'Series',
                'season':raw['seasons'][0],'episodes':[{'number':1,'title':'Missing',
                'overview':'','air_date':'2026-01-01',
                'still':'https://image.tmdb.org/t/p/original/example.jpg'}]},catalogue,2)
            local=build_series(12,[episode()],expected_total=1)
            window=module.SeriesPreview();window.catalogue=catalogue
            window.catalogue_client=Mock();window.catalogue_client.season.return_value=detail
            window.catalogue_cache=Mock();window.catalogue_loaded={};window.catalogue_base=local
            from series_adapter import SeriesSnapshot
            window.snapshot=SeriesSnapshot(local,'Series','',(),None,None,'','',456)
            window.selection=SeriesSelection(local)
            window.setProperty=Mock();window.queue_catalogue_art=Mock()
            window.load_catalogue_season(2)
            window.queue_catalogue_art.assert_called_once()
            window.catalogue_cache.localize.assert_not_called()
            self.assertEqual(window.catalogue_loaded[2].episodes[0].still,'')

if __name__=='__main__':unittest.main()
