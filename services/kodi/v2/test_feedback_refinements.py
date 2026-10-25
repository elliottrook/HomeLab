from pathlib import Path
import unittest
from unittest.mock import Mock,patch
import xml.etree.ElementTree as ET
from feedback_refinements import video_osd,media_header,search_hero,browser_rail,ROUTES
from build_global_search import build
from build_music_integration import transformed
import test_lab_runtime as runtime_tests
from tools.deploy_feedback_bundle import allowed
import tempfile

HERE=Path(__file__).parent

class FeedbackLayoutTests(unittest.TestCase):
    def test_osd_gradient_is_subtle_and_has_no_hard_flipped_edge(self):
        source=(HERE.parent/'skin.asterhome/1080i/VideoOSD.xml').read_bytes()
        root=ET.fromstring(video_osd(source))
        image=next(c for c in root.findall('.//control') if (c.findtext('texture') or '').endswith('ui-hero-bottom-fade.png'))
        self.assertNotIn('flipy',image.find('texture').attrib)
        self.assertEqual(image.findtext('colordiffuse'),'7a000000')
        self.assertLess(int(image.findtext('top')),0)
        original=ET.fromstring(source)
        for button in original.findall(".//control[@type='button']"):
            new=root.find(".//control[@id='%s']"%button.get('id'))
            self.assertEqual(ET.tostring(button),ET.tostring(new))

    def test_youtube_moves_to_compact_header_and_does_not_overlap_search(self):
        with tempfile.TemporaryDirectory() as directory:
            stage=Path(directory)/'search';build(stage,True,True,'aster-global-search-ui12')
            root=ET.fromstring(media_header((stage/'overlay/Home.xml').read_bytes()))
        order=(130,131,132,133,134,136,135);edge=0
        for identity in order:
            node=root.find(".//control[@id='%s']"%identity)
            self.assertGreater(int(node.findtext('left')),edge)
            edge=int(node.findtext('left'))+int(node.findtext('width'))
        self.assertLess(edge,1750)
        self.assertEqual(root.findtext(".//control[@id='136']/label"),'YouTube')
        self.assertEqual(root.findtext(".//control[@id='134']/onright"),'136')
        self.assertEqual(root.findtext(".//control[@id='135']/onleft"),'136')

    def test_music_bar_spans_entire_canvas_behind_logo(self):
        root=ET.fromstring(transformed()['1080i/IncludesMusic.xml'])
        group=next(g for g in root.iter('control') if g.find("control[@id='110']") is not None)
        images=group.findall("control[@type='image']");bar=images[0]
        self.assertEqual(tuple(bar.findtext(k) for k in ('left','width','height')),('0','1920','160'))
        self.assertTrue(images[1].findtext('texture').endswith('29-aster-music-logo.png'))

    def test_both_music_browser_rail_states_share_six_centred_destinations(self):
        root=ET.fromstring(browser_rail((HERE/'script.astermusic.v2lab/resources/skins/Default/1080i/MusicLab.xml').read_bytes()))
        group=next(g for g in root.iter('control') if g.find("control[@id='9007']") is not None)
        self.assertEqual(tuple(int(c.get('id')) for c in group.findall("control[@type='button']")),ROUTES)
        self.assertNotIn('aster-compass-128.png',ET.tostring(group).decode())
        buttons=group.findall("control[@type='button']")
        self.assertEqual((int(buttons[0].findtext('top'))+int(buttons[-1].findtext('top'))+62)/2,310)

    def test_search_hero_preserves_existing_buttons(self):
        source=(HERE/'search_native/overlay/custom_1128_searchdetails.xml').read_bytes()
        root=ET.fromstring(search_hero(source))
        self.assertIsNotNone(root.find(".//control[@id='10']"))
        self.assertIn('AsterSearch.DetailHero',ET.tostring(root).decode())

    def test_episode_list_has_no_bottom_wrap(self):
        root=ET.parse(HERE/'series_preview/resources/skins/Default/1080i/SeriesPreview.xml')
        self.assertEqual(root.findtext(".//control[@id='300']/ondown"),'noop')

    def test_deployment_rejects_profile_production_and_arbitrary_targets(self):
        for path in ('../outside','.kodi/userdata/guisettings.xml','.kodi/addons/plugin.video.jellyfin/default.py',
                     '.aster-staging/arbitrary/default.py','/storage/.kodi/addons/skin.asterhome/1080i/Home.xml'):
            self.assertFalse(allowed(path),path)
        self.assertTrue(allowed('.kodi/addons/skin.asterhome/1080i/Home.xml'))

class BrowserLifecycleTests(unittest.TestCase):
    setUp=runtime_tests.RuntimeTests.setUp
    def test_home_exit_closes_hidden_browser_instead_of_retaining_lock(self):
        self.window.browser_identity=13000;self.window.show=Mock()
        self.gui.getCurrentWindowId.return_value=10000
        self.gui.Window.return_value.getProperty.return_value=''
        self.xbmc.getCondVisibility.return_value=False
        self.xbmc.Monitor.return_value.abortRequested.return_value=False
        with patch.object(self.runtime,'rpc',return_value=[]) as read:
            self.window.browse()
        self.assertTrue(self.window.finished);self.assertTrue(self.window.closed)
        read.assert_called_once_with('Player.GetActivePlayers',{})
