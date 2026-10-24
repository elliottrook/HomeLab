import hashlib
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

from player_controls import PAGES,SKIN,build,page


class SharedControlsTests(unittest.TestCase):
    def test_all_four_player_families_are_present(self):
        self.assertEqual(set(PAGES),{'VideoOSD.xml','custom_1121_albumplayer.xml','MyMusicNav.xml','custom_1111_digest.xml'})

    def test_exact_actions_navigation_and_visibility_are_preserved(self):
        fields=('onclick','onleft','onright','onup','ondown','visible','enable','label')
        for name in PAGES:
            source=(SKIN/'1080i'/name).read_bytes();old=ET.fromstring(source);new=ET.fromstring(page(name,source))
            for identity in PAGES[name]['icons']:
                with self.subTest(page=name,control=identity):
                    original=old.find(f'.//control[@type="button"][@id="{identity}"]')
                    changed=new.find(f'.//control[@type="button"][@id="{identity}"]')
                    for field in fields:
                        self.assertEqual([(n.text,n.attrib) for n in original.findall(field)],
                                         [(n.text,n.attrib) for n in changed.findall(field)])
                    self.assertFalse(changed.findtext('texturefocus'));self.assertFalse(changed.findtext('texturenofocus'))
                    self.assertEqual(changed.findtext('textcolor'),'00000000')
            for hook in ('onload','onunload','defaultcontrol'):
                self.assertEqual([(n.text,n.attrib) for n in old.findall(hook)],[(n.text,n.attrib) for n in new.findall(hook)])

    def test_every_control_target_and_glyph_fits_declared_row(self):
        for name,config in PAGES.items():
            new=ET.fromstring(page(name,(SKIN/'1080i'/name).read_bytes()))
            left,width=config['frame']
            ids=[node.get('id') for node in new.findall('.//control') if node.get('id')]
            self.assertEqual(len(ids),len(set(ids)))
            for slot in config['slots']:
                for identity in slot:
                    control=new.find(f'.//control[@id="{identity}"]')
                    self.assertGreaterEqual(int(control.findtext('left')),left)
                    self.assertLessEqual(int(control.findtext('left'))+int(control.findtext('width')),left+width)
                    self.assertGreaterEqual(int(control.findtext('width')),44)

    def test_bundle_determinism_assets_and_no_source_mutation(self):
        before={name:hashlib.sha256((SKIN/'1080i'/name).read_bytes()).hexdigest() for name in PAGES}
        with tempfile.TemporaryDirectory() as one,tempfile.TemporaryDirectory() as two:
            first=build(one);second=build(two);self.assertEqual(first['sha256'],second['sha256'])
            self.assertEqual(first['source_sha256'],before)
            with zipfile.ZipFile(Path(one)/first['archive']) as package:
                self.assertIsNone(package.testzip())
                for name in PAGES:
                    root=ET.fromstring(package.read('1080i/'+name))
                    for node in root.findall('.//texture'):
                        if (node.text or '').startswith('special://skin/media/player-controls/'):
                            asset=node.text.replace('special://skin/','')
                            self.assertIn(asset,package.namelist())
                self.assertFalse(any(name.startswith(('tools/','addon.xml')) for name in package.namelist()))
        self.assertEqual(before,{name:hashlib.sha256((SKIN/'1080i'/name).read_bytes()).hexdigest() for name in PAGES})


if __name__=='__main__':unittest.main()
