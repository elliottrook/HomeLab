import importlib.util,sys,tempfile,unittest,xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
from branding_rails import header,settings,extend_search
from canonical_sound_balance import build,samples

HERE=Path(__file__).parent
class BrandingTests(unittest.TestCase):
    def test_each_header_has_fitted_capsule_search_and_preserved_actions(self):
        cases=(('IncludesBooks.xml',(110,111,112),(180,220,180)),('IncludesMusic.xml',(110,111,112,113,114),(180,180,170,180,170)),
            ('custom_1111_digest.xml',(310,311,301),(210,220,150)),('custom_1112_home.xml',(300,301),(170,170)))
        for name,ids,widths in cases:
            original=(HERE.parent/'skin.asterhome/1080i'/name).read_bytes();old=ET.fromstring(original)
            if name=='IncludesMusic.xml':
                group=next(g for g in old.iter() if g.find('control[@id="110"]') is not None)
                if group.find('control[@id="114"]') is None:
                    node=ET.SubElement(group,'control',dict(type='button',id='114'))
                    for k,v in dict(left=1233,top=28,label='Genres',onclick='RunScript(genres)').items():ET.SubElement(node,k).text=str(v)
                original=ET.tostring(old)
            root=ET.fromstring(header(original,ids,widths,500));search=root.find('.//control[@id="139"]')
            self.assertEqual(search.findtext('left'),'350');self.assertEqual(search.findtext('width'),'170')
            self.assertEqual(search.findtext('onright'),str(ids[0]));self.assertIn('ui22',search.findtext('onclick'))
            for i in ids:
                b=root.find(f'.//control[@id="{i}"]');prior=old.find(f'.//control[@id="{i}"]')
                self.assertEqual(b.findtext('onclick'),prior.findtext('onclick'));self.assertEqual(b.findtext('top'),'31')
                self.assertEqual(b.find('texturefocus').get('colordiffuse'),'ff005c46')
            self.assertFalse(any(c.findtext('width','').isdigit() and int(c.findtext('width'))>1500 and c.findtext('height') in ('142','160','180') for c in root.findall('.//control[@type="image"]')))
            gold=[t for t in root.iter('texture') if t.get('colordiffuse')=='ffad8a4d'];self.assertEqual(len(gold),1)
    def test_settings_has_all_existing_areas_local_status_and_side_rail(self):
        old=(HERE.parent/'skin.asterhome/1080i/Settings.xml').read_bytes();root=ET.fromstring(settings(old))
        self.assertIsNotNone(root.find('.//include[@content="AsterNavigationRail"]'))
        self.assertEqual(len(root.findall('.//control[@type="button"]')),9)
        text=ET.tostring(root).decode();self.assertIn('Network.IPAddress',text);self.assertIn('System.ScreenResolution',text)
        self.assertNotIn('type="panel"',text);self.assertNotIn('limestone',text)
        defined={n.text for n in ET.fromstring((HERE.parent/'skin.asterhome/1080i/Font.xml').read_bytes()).iter('name')}
        self.assertTrue(all(n.text in defined for n in root.iter('font')))
        for item in ET.fromstring(old).findall('.//content/item'):self.assertIn(item.findtext('onclick'),text)
    def test_search_admission_is_bounded_and_restores_original_page(self):
        original=(HERE/'search_native/default.py').read_bytes();updated=extend_search(original).decode()
        compile(updated,'search','exec')
        self.assertIn('source_window in (10000,10004,11110',updated)
        self.assertIn('not rpc(\'Player.GetActivePlayers\')',updated)
        self.assertIn('getCurrentWindowId()==source_window',updated)
        self.assertNotIn("executebuiltin('ActivateWindow(Home)')",updated)
    def test_balance_preserves_right_samples_timing_and_mirrored_panning(self):
        source=HERE.parent/'resource.uisounds.asterhome/resources'
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'balanced';result=build(source,out)
            self.assertLess(result['left_gain'],1);self.assertEqual(result['right_gain'],1)
            for row in result['files']:
                a=samples((source/row['file']).read_bytes());b=samples((out/'masters'/row['file']).read_bytes())
                self.assertEqual(len(a),len(b));self.assertEqual(a[1::2],b[1::2])
                self.assertLessEqual(max(map(abs,b)),max(map(abs,a)))
            sides={r['file']:r['lr_db'] for r in result['files']}
            self.assertAlmostEqual(sides['nav-left.wav'],-sides['nav-right.wav'],places=4)
            self.assertTrue(all(abs(db)<.2 for n,db in sides.items() if n not in ('nav-left.wav','nav-right.wav')))
            with self.assertRaisesRegex(ValueError,'immutable'):build(source,out)
    def test_balanced_deployment_pins_match_generated_runtime(self):
        modules=[]
        for name in ('deploy_canonical_clicks','deploy_balanced_clicks'):
            spec=importlib.util.spec_from_file_location(name,HERE/'tools'/(name+'.py'))
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);modules.append(module)
        engine=SimpleNamespace(EXPECTED={'old':'runtime'})
        with patch.dict(sys.modules,{'deploy_canonical_clicks':modules[0]}):modules[1].configure(engine)
        self.assertEqual(engine.ORIGINALS['AsterTV'],{'old':'runtime'});self.assertEqual(len(engine.ORIGINALS['AsterTVProd']),7)
        with tempfile.TemporaryDirectory() as d:
            result=build(HERE.parent/'resource.uisounds.asterhome/resources',Path(d)/'balanced')
            self.assertEqual({r['file']:r['runtime_sha256'] for r in result['files']},engine.EXPECTED)
            self.assertEqual({r['file']:r['master_sha256'] for r in result['files']},engine.MASTER_EXPECTED)
            self.assertEqual(result['left_gain'],engine.TRANSFORM['left_gain'])
    def test_release_packaging_can_select_balanced_runtime_explicitly(self):
        import zipfile
        sys.path.insert(0,str(HERE.parent))
        import package_aster_home
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);balanced=build(HERE.parent/'resource.uisounds.asterhome/resources',out/'expected')
            record=package_aster_home.build_archive('resource.uisounds.asterhome',out,runtime_sounds=True,balanced_sounds=True)
            with zipfile.ZipFile(out/record['archive']) as archive:
                for r in balanced['files']:
                    self.assertEqual(archive.read('resource.uisounds.asterhome/resources/'+r['file']),(out/'expected/resources'/r['file']).read_bytes())
            with self.assertRaisesRegex(ValueError,'require runtime'):package_aster_home.build_archive('resource.uisounds.asterhome',out,balanced_sounds=True)
