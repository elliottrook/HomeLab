from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from media_hero_home import (IDLE, transform, update_family_manifest,
                             update_search_manifest)


HERE = Path(__file__).resolve().parent


class MediaHeroHomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (HERE/'baselines/aster-family-recovery7b-Home.xml').read_bytes()
        cls.root = ET.fromstring(transform(raw))

    def test_accepted_header_destinations_are_preserved(self):
        for identity, label in ((135, 'Search'), (136, 'YouTube'),
                                (137, 'Requests')):
            self.assertEqual(
                self.root.find(f".//control[@id='{identity}']").findtext('label'),
                label)

    def test_owned_recommendation_source_and_timer_are_installed(self):
        self.assertIn('hero-tick', self.root.findtext('onload'))
        self.assertEqual(self.root.findtext('onunload'),
                         'CancelAlarm(AsterMediaHero,silent)')
        source = self.root.find(".//control[@id='101']")
        self.assertEqual(source.findtext('content'),
                         'plugin://plugin.video.asterhome/?mode=recommended')
        self.assertIsNone(source.find('visible'))
        recent = self.root.find(".//control[@id='110']")
        self.assertEqual(recent.findtext('content'),
                         'plugin://plugin.video.asterhome/?mode=recent')
        self.assertEqual(len([node for node in self.root.findall(".//control[@type='label']")
                              if node.findtext('label') == 'Recently Added']), 1)

    def test_compact_actions_exist_only_for_idle_recommendation(self):
        expected = ((120, '180'), (121, '165'), (122, '120'))
        for identity, width in expected:
            control = self.root.find(f".//control[@id='{identity}']")
            self.assertEqual(control.findtext('visible'), IDLE)
            self.assertEqual(control.findtext('width'), width)
            self.assertEqual(control.findtext('height'), '44')
            self.assertEqual(control.findtext('font'), 'font20')
        self.assertEqual(self.root.find(".//control[@id='122']").findtext('onclick'),
                         'Control.Move(101,1)')

    def test_synopsis_is_larger_and_actions_use_recommendation_identity(self):
        hero = self.root.find(".//control[@id='21']")
        synopsis = next(node for node in hero.findall('control')
                        if node.get('type') == 'textbox')
        self.assertEqual((synopsis.findtext('font'), synopsis.findtext('height')),
                         ('font20', '86'))
        self.assertEqual(synopsis.findtext('top'), '318')
        rating = next(node for node in hero.findall('control')
                      if node.findtext('label', '').endswith('[AsterHeroRating]'))
        self.assertEqual(rating.findtext('top'), '408')
        self.assertEqual(hero.find("control[@id='122']").findtext('top'), '442')
        play = hero.find("control[@id='120']")
        self.assertEqual(len(play.findall('onclick')), 2)
        self.assertTrue(all('$VAR[AsterHeroKind]' in node.get('condition', '')
                            for node in play.findall('onclick')))

    def test_unknown_predecessor_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'media-hero-home-predecessor'):
            transform(b'<window/>')

    def test_search_scopes_and_integrity_manifests_are_composed(self):
        search = (HERE/'search_native/overlay/custom_1127_search.xml').read_bytes()
        root = ET.fromstring(search)
        self.assertEqual(root.find(".//control[@id='50']").findtext('label'),
                         'Search library')
        self.assertEqual(root.find(".//control[@id='51']").findtext('label'),
                         'Search catalogue')
        self.assertEqual(root.find(".//control[@id='51']").findtext('onclick'),
                         'RunScript(script.asterseerr)')
        search_manifest = update_search_manifest(
            (HERE/'baselines/aster-global-search-ui22-manifest.json').read_bytes(),
            search)
        family = update_family_manifest(
            (HERE/'baselines/aster-family-runtime-manifest.json').read_bytes(),
            ET.tostring(self.root, encoding='utf-8', xml_declaration=True),
            search, search_manifest)
        accepted = __import__('json').loads(family)
        self.assertEqual(
            accepted['skin']['1080i/custom_1127_search.xml'],
            __import__('hashlib').sha256(search).hexdigest())
        self.assertEqual(
            accepted['components']['aster-global-search-ui22']['manifest_sha256'],
            __import__('hashlib').sha256(search_manifest).hexdigest())


if __name__ == '__main__':
    unittest.main()
