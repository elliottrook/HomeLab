import ast
import unittest
import xml.etree.ElementTree as ET

from music_hero_ui import extend_home, extend_includes, extend_music_data


class MusicHeroUiTests(unittest.TestCase):
    def test_runtime_adds_owned_hero_without_implicit_play(self):
        source = b'''from aster_v2_music import handoff, restore_focus
def main(page, action='load'):
    import xbmc
    import xbmcgui
    import xbmcvfs
    if page == 'music-player':
        return
    window.setProperty('AsterMusic.LoadReady', 'true')
'''
        result = extend_music_data(source).decode()
        ast.parse(result)
        self.assertIn("if page == 'home' and action.startswith('hero-')", result)
        self.assertIn("if action == 'hero-play'", result)
        self.assertIn("if action == 'hero-tick' and window.getFocusId() == 500", result)
        self.assertNotIn("action == 'load':\n            play_album", result)

    def test_template_uses_recommendation_only_off_the_tile_grid(self):
        source = b'''<includes><include name="AsterMusicPage"><param name="gridup" default="111"/><definition>
<control type="image"><texture>$INFO[Container(500).ListItem.Art(fanart)]</texture></control>
<control type="group">
<control type="label"><top>163</top><label>$PARAM[heading]</label></control>
<control type="label"><top>214</top><label>$INFO[Container(500).ListItem.Label]</label></control>
<control type="textbox"><top>288</top><label>$INFO[Container(500).ListItem.Property(AsterMusic.Summary)]</label></control>
<control type="label"><top>386</top><label>$INFO[Window.Property(AsterMusic.Status)]</label></control>
<control type="button" id="110"><ondown>500</ondown></control><control type="button" id="111"><ondown>500</ondown></control>
<control type="button" id="112"><ondown>500</ondown></control><control type="button" id="113"><ondown>500</ondown></control>
<control type="button" id="114"><ondown>500</ondown></control><control type="button" id="139"><ondown>500</ondown></control>
<control type="panel" id="500"><onup>111</onup></control>
<control type="button" id="115"><onclick>old</onclick></control>
</control></definition></include></includes>'''
        root = ET.fromstring(extend_includes(source))
        panel = root.find(".//control[@id='500']")
        self.assertEqual(panel.findtext('onup'), '$PARAM[gridup]')
        for identity in (110, 111, 112, 113, 114, 139):
            self.assertEqual(root.find(".//control[@id='%s']/ondown" % identity).text,
                             '$PARAM[topdown]')
        self.assertEqual(root.find(".//control[@id='116']/onclick").text,
                         'RunScript(special://skin/tools/music_data.py,home,hero-play)')
        visible = root.find(".//control[@id='116']/visible").text
        self.assertIn('!Control.HasFocus(500)', visible)
        self.assertEqual(root.find(".//control[@id='115']/onclick").text,
                         'RunScript(special://skin/tools/aster_v2_music.py,shuffle,home)')

    def test_home_starts_on_navigation_and_bounds_rotator(self):
        source = b'''<window><defaultcontrol always="true">500</defaultcontrol>
<onload>existing</onload><controls><include content="AsterMusicPage">
<param name="gridup" value="115"/></include></controls></window>'''
        root = ET.fromstring(extend_home(source))
        self.assertEqual(root.findtext('defaultcontrol'), '110')
        params = {node.get('name'): node.get('value')
                  for node in root.findall('.//include/param')}
        self.assertEqual(params['gridup'], '116')
        self.assertEqual(params['topdown'], '116')
        self.assertTrue(any('00:12' in (node.text or '') for node in root.findall('onload')))
        self.assertEqual(root.findtext('onunload'), 'CancelAlarm(AsterMusicHero,silent)')


if __name__ == '__main__':
    unittest.main()
