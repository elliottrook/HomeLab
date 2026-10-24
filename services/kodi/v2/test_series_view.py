import ast,unittest,tempfile,importlib.util,sys
from unittest.mock import Mock,patch
from pathlib import Path
import xml.etree.ElementTree as ET
from series_model import build_series
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

    def test_empty_and_unknown_values_do_not_invent_content(self):
        view=SeriesSelection(build_series(12,[],expected_total=0))
        self.assertIsNone(view.episode);self.assertFalse(view.change_season(0));view.select(0)
        row=build_series(12,[episode(1,None,None)],expected_total=1).seasons[0].episodes[0]
        self.assertEqual(episode_metadata(row),'Episode number unavailable · Duration unavailable · Air date unavailable')

    def test_native_layout_has_stable_rows_and_no_heavy_row_boxes(self):
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
        for layout in (rows.find('itemlayout'),rows.find('focusedlayout')):
            titles=[c for c in layout.findall('control') if c.findtext('label')=='$INFO[ListItem.Label]']
            self.assertEqual(len(titles),2)
            selected=next(c for c in titles if c.findtext('textcolor')=='ff005c46')
            self.assertEqual(selected.findtext('visible'),'String.IsEqual(ListItem.Property(Selected),true)')

    def test_preview_dispatch_has_no_playback_or_server_writes(self):
        source=(HERE/'series_preview/default.py').read_text();ast.parse(source)
        self.assertNotIn('Player.Open',source);self.assertNotIn('PlayMedia(',source)
        self.assertNotIn('urllib',source);self.assertNotIn('requests.',source)
        self.assertNotIn('assert ',source)

    def test_preview_build_is_deterministic_and_refuses_overwrite(self):
        import json,hashlib
        with tempfile.TemporaryDirectory() as parent:
            first=Path(parent)/'one';second=Path(parent)/'two'
            self.assertEqual(build(first),build(second))
            manifest=json.loads((first/'manifest.json').read_text())
            self.assertEqual(len(manifest['files']),5)
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

if __name__=='__main__':unittest.main()
