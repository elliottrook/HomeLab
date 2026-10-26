from copy import deepcopy
from datetime import timedelta
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from build_home_preview import build,layout
from home_dashboard_model import project
from home_preview_source import read_payload,MAX_BYTES
from test_home_freshness import NOW,feed

HERE=Path(__file__).parent


def fixture():
    payload=feed()
    payload['snapshot']=dict(schema_version=3,snapshot_id='ha-home-pilot-v3',
        lights=[dict(alias='laundry lights',state='on')],
        temperatures=[dict(alias='closet temperature',value=20.5,unit='°C')],
        weather=[dict(alias='home weather',condition='sunny',temperature=15,unit='°C',humidity=60)],
        rooms=[],entities=[],timers=[],media_providers=[])
    return payload


class HomeModelTests(unittest.TestCase):
    def test_reviewed_export_projects_four_read_only_groups(self):
        view=project(fixture(),NOW)
        self.assertEqual(view.state,'fresh')
        self.assertEqual([g.name for g in view.groups],['Lighting','Comfort','Cameras','Timers'])
        self.assertEqual(view.groups[0].details,('Laundry lights · On',))
        self.assertIn('20.5°C',' '.join(view.groups[1].details))
        self.assertEqual(view.exceptions,2)

    def test_old_or_missing_feed_hides_values_even_if_snapshot_bad(self):
        payload=fixture();payload['source_updated_at']=(NOW-timedelta(days=3)).isoformat()
        payload['snapshot']['lights'][0]['state']='SECRET-STALE-STATE'
        for value,state in ((payload,'stale'),(None,'missing'),({},'invalid')):
            view=project(value,NOW)
            self.assertEqual(view.state,state)
            self.assertNotIn('SECRET',repr(view))
            self.assertNotIn('20.5',repr(view))
            self.assertEqual(view.exceptions,4)

    def test_freshness_expires_while_open_without_reloading(self):
        payload=fixture()
        self.assertEqual(project(payload,NOW).state,'fresh')
        self.assertEqual(project(payload,NOW+timedelta(seconds=601)).state,'stale')

    def test_unknown_alias_or_field_is_refused(self):
        for key,value in (('alias','unreviewed room'),('url','https://example.org/frame')):
            payload=fixture();payload['snapshot']['lights'][0][key]=value
            self.assertEqual(project(payload,NOW).state,'invalid')
        payload=fixture();payload['snapshot']['rooms']=['private room']
        self.assertEqual(project(payload,NOW).state,'invalid')
        payload=fixture();payload['token']='not-a-real-token'
        self.assertEqual(project(payload,NOW).state,'invalid')

    def test_camera_metadata_never_becomes_live_view_or_status_claim(self):
        payload=fixture();payload['snapshot']['cameras']=[dict(alias='Front of house',status='online')]
        camera=project(payload,NOW).groups[2]
        self.assertEqual(camera.state,'unavailable')
        self.assertNotIn('online',repr(camera))
        self.assertFalse(hasattr(camera,'action'))
        self.assertFalse(hasattr(camera,'url'))

    def test_value_ranges_units_and_types(self):
        for value in (True,math.nan,math.inf,61,-51,10**400,'20'):
            payload=fixture();payload['snapshot']['temperatures'][0]['value']=value
            self.assertEqual(project(payload,NOW).state,'invalid')
        for humidity in (-1,101,True,math.nan,'60'):
            payload=fixture();payload['snapshot']['weather'][0]['humidity']=humidity
            self.assertEqual(project(payload,NOW).state,'invalid')

    def test_empty_values_are_not_fabricated_and_input_not_mutated(self):
        payload=fixture();payload['snapshot']['lights']=[];payload['snapshot']['temperatures']=[]
        payload['snapshot']['weather']=[];before=deepcopy(payload)
        view=project(payload,NOW)
        self.assertEqual(payload,before)
        self.assertEqual(view.exceptions,4)
        self.assertEqual(view.groups[0].summary,'No reviewed values')

    def test_collection_bounds_duplicate_alias_and_malformed_rows(self):
        for key,rows in (('lights',[dict(alias='laundry lights',state='on')]*2),
                ('temperatures',[dict(alias='closet temperature',value=10,unit='°C')]*2),
                ('weather',[None]),('cameras',[dict(alias='unknown',status='online')])):
            payload=fixture();payload['snapshot'][key]=rows
            self.assertEqual(project(payload,NOW).state,'invalid')


class HomePreviewTests(unittest.TestCase):
    def test_local_read_bounds_missing_bad_json_and_symlinks(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();path=root/'home.json'
            self.assertIsNone(read_payload(path))
            path.write_text(json.dumps(fixture()))
            self.assertEqual(read_payload(path),fixture())
            for raw in (b'{',b'\xff',b'x'*(MAX_BYTES+1)):
                path.write_bytes(raw);self.assertEqual(read_payload(path),{})
            link=root/'linked.json';link.symlink_to(path)
            self.assertEqual(read_payload(link),{})
            linked=root/'linked-dir';linked.symlink_to(root,target_is_directory=True)
            self.assertEqual(read_payload(linked/'home.json'),{})
            fifo=root/'fifo';os.mkfifo(fifo)
            self.assertEqual(read_payload(fifo),{})

    def test_grid_navigation_fonts_and_no_external_assets(self):
        xml=ET.fromstring(layout())
        expected={301:('302','303'),302:('200','304'),303:('304','noop'),304:('200','noop')}
        for identity,(right,down) in expected.items():
            node=xml.find(".//control[@id='%d']" % identity)
            self.assertEqual(node.findtext('onright'),right);self.assertEqual(node.findtext('ondown'),down)
        fonts={n.text for n in ET.parse(HERE.parent/'skin.asterhome/1080i/Font.xml').findall('.//name')}
        self.assertTrue(all(n.text in fonts for n in xml.findall('.//font')))
        self.assertTrue(all('http' not in (n.text or '') for n in xml.findall('.//texture')))
        self.assertFalse(xml.findall('.//onclick'))
        for identity in (200,201):
            texture=xml.find(".//control[@id='%d']/texturenofocus" % identity)
            self.assertEqual(texture.get('colordiffuse'),'60000000')

    def test_immutable_five_member_bundle_and_no_runtime_device_commands(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'bundle';pin=build(root)
            manifest=json.loads((root/'manifest.json').read_text())
            self.assertEqual(len(manifest['files']),5)
            self.assertEqual(hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(),pin)
            for row in manifest['files']:
                self.assertEqual(hashlib.sha256((root/row['path']).read_bytes()).hexdigest(),row['sha256'])
            with self.assertRaises(ValueError):build(root)
        script=(HERE/'home_preview/default.py').read_text()
        for banned in ('Player.Open','Player.Stop','PlayMedia(','ActivateWindow(',
                'urllib','requests','subprocess','call_service','camera_tick','timer_1'):
            self.assertNotIn(banned,script)

    def test_external_pin_payload_drift_and_link_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()/'bundle';pin=build(root)
            spec=importlib.util.spec_from_file_location('test_home_preview',root/'default.py')
            module=importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules,xbmc=types.ModuleType('xbmc'),xbmcgui=types.SimpleNamespace(WindowXML=object)):
                spec.loader.exec_module(module)
            module.verify(pin)
            with self.assertRaises(ValueError):module.verify('0'*64)
            member=root/'resources/lib/home_freshness.py';raw=member.read_bytes();member.write_bytes(raw+b'\n')
            with self.assertRaises(ValueError):module.verify(pin)
            member.unlink();other=root/'other.py';other.write_bytes(raw);member.symlink_to(other)
            with self.assertRaises(ValueError):module.verify(pin)


if __name__=='__main__':unittest.main()
