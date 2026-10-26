import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from home_design import build, arc_svg

SOURCE=Path(__file__).resolve().parents[1]/'skin.asterhome/1080i/custom_1112_home.xml'

class HomeDesignTests(unittest.TestCase):
    def setUp(self):
        self.old=ET.fromstring(SOURCE.read_bytes())
        self.root=ET.fromstring(build(SOURCE.read_bytes()))

    def test_lifecycle_and_identity_unchanged(self):
        self.assertEqual(self.old.attrib,self.root.attrib)
        for tag in ('onload','onunload','backgroundcolor'):
            self.assertEqual(self.old.findtext(tag),self.root.findtext(tag))

    def test_unique_controls_and_resolvable_focus(self):
        ids=[n.get('id') for n in self.root.iter('control') if n.get('id')]
        self.assertEqual(len(ids),len(set(ids)))
        for n in self.root.iter('control'):
            for key in ('onup','ondown','onleft','onright'):
                target=n.findtext(key)
                if target and target.isdecimal():
                    self.assertIn(target,ids+['8999'])

    def test_presets_camera_and_refresh_keep_existing_actions(self):
        for identity in (300,302,303,304,305):
            query=f'.//control[@id="{identity}"]/onclick'
            self.assertEqual(self.old.findtext(query),self.root.findtext(query))
        self.assertEqual(self.root.findtext('.//control[@id="306"]/onclick'),
                         'RunScript(special://skin/tools/hub_data.py,home,timer_stop)')

    def test_no_dots_stone_or_new_remote_service_actions(self):
        text=ET.tostring(self.root).decode()
        self.assertNotIn('AsterTimerRing',text)
        self.assertNotIn('stone-pill',text)
        self.assertNotIn('http',text)
        self.assertNotIn('home,play',text)
        self.assertIn('Seconds sweep',text)
        self.assertEqual(self.root.findtext('.//control[@id="500"]/onclick'),'noop')

    def test_fonts_and_screen_bounds(self):
        fonts=ET.parse(SOURCE.parent/'Font.xml')
        names={n.text for n in fonts.findall('.//name')}
        for n in self.root.iter('control'):
            if n.find('font') is not None:self.assertIn(n.findtext('font'),names)
            for pos,size,limit in (('left','width',1920),('top','height',1080)):
                p,s=n.findtext(pos),n.findtext(size)
                if p and s and p.isdecimal() and s.isdecimal():
                    self.assertLessEqual(int(p)+int(s),limit)

    def test_arc_endpoints_and_bounds(self):
        for seconds in range(61):
            root=ET.fromstring(arc_svg(seconds))
            circles=list(root)
            self.assertEqual(len(circles),1 if seconds==0 else 2)
            if seconds:
                length=float(circles[1].get('stroke-dasharray').split()[0])
                self.assertAlmostEqual(length,2*math.pi*226*seconds/60,places=5)
            self.assertNotIn('<text',arc_svg(seconds))
        for bad in (-1,61,True,0.5,'1'):
            with self.assertRaises(ValueError):arc_svg(bad)

    def test_arc_and_countdown_center_aligned(self):
        arc=next(n for n in self.root.iter('control') if 'arc-$INFO' in n.findtext('texture',''))
        clock=next(n for n in self.root.iter('control') if n.findtext('font')=='font80')
        center=lambda n:int(n.findtext('left'))+int(n.findtext('width'))/2
        self.assertEqual(center(arc),center(clock))
        for i in (303,304,305):
            self.assertGreater(int(self.root.findtext(f'.//control[@id="{i}"]/top')),900)

if __name__=='__main__':unittest.main()
