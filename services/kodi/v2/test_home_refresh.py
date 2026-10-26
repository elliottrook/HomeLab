from datetime import timedelta
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import home_refresh
from home_refresh import Consumer,probe,read_generation
from test_home_freshness import NOW
from test_home_preview import fixture


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.path=self.root/'home.json'
        self.consumer=Consumer(self.path)

    def write(self,value=None,raw=None):
        p=self.root/'next';p.write_bytes(raw if raw is not None else json.dumps(value or fixture()).encode())
        p.chmod(0o600);os.replace(p,self.path)

    def test_initial_load_and_unchanged_stamps_do_not_reread(self):
        self.write()
        with patch.object(home_refresh,'read_generation',wraps=read_generation) as read:
            self.assertEqual(self.consumer.update(NOW,0).state,'fresh')
            for elapsed in range(1,30):self.consumer.update(NOW+timedelta(seconds=elapsed),elapsed)
            self.assertEqual(read.call_count,1)
        self.assertEqual((self.consumer.reads,self.consumer.generations),(1,1))

    def test_replacement_changes_values_and_duplicate_generation_is_not_new(self):
        self.write();self.consumer.update(NOW,0)
        value=fixture();value['generated_at']=NOW.isoformat();value['snapshot']['lights'][0]['state']='off'
        self.write(value);view=self.consumer.update(NOW,2)
        self.assertEqual(view.groups[0].details,('Laundry lights · Off',))
        self.assertEqual(self.consumer.generations,2)
        self.write(value);self.consumer.update(NOW,4)
        self.assertEqual((self.consumer.reads,self.consumer.generations),(3,2))

    def test_poll_limit_and_force_reload(self):
        self.write();self.consumer.update(NOW,10)
        value=fixture();value['generated_at']=NOW.isoformat();self.write(value)
        self.consumer.update(NOW,11.99);self.assertEqual(self.consumer.reads,1)
        self.consumer.update(NOW,11.99,force=True);self.assertEqual(self.consumer.reads,2)
        self.consumer.update(NOW,12);self.assertEqual(self.consumer.reads,2)

    def test_expiry_happens_in_memory_without_disk_read(self):
        self.write();self.consumer.update(NOW,0)
        with patch.object(home_refresh,'probe',side_effect=AssertionError('unexpected-probe')):
            view=self.consumer.update(NOW+timedelta(seconds=601),1)
        self.assertEqual(view.state,'stale');self.assertNotIn('20.5',repr(view))
        self.assertEqual(self.consumer.reads,1)

    def test_missing_invalid_and_recovery_do_not_keep_displaying_old_values(self):
        self.write();self.consumer.update(NOW,0);self.path.unlink()
        self.assertEqual(self.consumer.update(NOW,2).state,'missing')
        self.write(raw=b'{"private-unknown":"TOKEN"}')
        self.assertEqual(self.consumer.update(NOW,4).state,'invalid')
        self.assertEqual(self.consumer.payload,{})
        self.assertNotIn('TOKEN',repr(self.consumer.__dict__))
        self.write();self.assertEqual(self.consumer.update(NOW,6).state,'fresh')
        self.assertEqual(self.consumer.generations,1)

    def test_older_source_and_older_publication_are_refused(self):
        self.write();self.consumer.update(NOW,0)
        for i,key in enumerate(('source_updated_at','generated_at')):
            value=fixture();value[key]=(NOW-timedelta(seconds=60)).isoformat()
            if key=='generated_at':value['source_updated_at']=(NOW-timedelta(seconds=1)).isoformat()
            self.write(value);view=self.consumer.update(NOW,2+i*2)
            self.assertEqual(view.state,'invalid');self.assertEqual(self.consumer.load_status,'older-generation')
        self.write();self.assertEqual(self.consumer.update(NOW,6).state,'fresh')

    def test_old_source_cannot_be_revived_by_recopy(self):
        self.write();self.consumer.update(NOW,0)
        value=fixture();value['source_updated_at']=(NOW-timedelta(days=1)).isoformat()
        value['generated_at']=NOW.isoformat();self.write(value)
        self.assertEqual(self.consumer.update(NOW,2).state,'stale')
        self.assertEqual(self.consumer.payload['snapshot'],{'schema_version':3})

    def test_symlink_parent_hardlink_permissions_oversize_and_fifo(self):
        self.write();self.consumer.update(NOW,0)
        self.path.chmod(0o644);self.assertEqual(self.consumer.update(NOW,2).state,'invalid')
        self.path.chmod(0o600);hard=self.root/'hard';os.link(self.path,hard)
        self.assertEqual(probe(self.path)[0],'invalid');hard.unlink()
        linked=self.root/'link';linked.symlink_to(self.root,target_is_directory=True)
        self.assertEqual(probe(linked/'home.json')[0],'invalid')
        self.path.unlink();self.path.symlink_to(hard)
        self.assertEqual(self.consumer.update(NOW,4).state,'invalid')
        self.path.unlink();os.mkfifo(self.path)
        self.assertEqual(self.consumer.update(NOW,6).state,'invalid')
        self.path.unlink();self.write(raw=b'x'*262145)
        self.assertEqual(self.consumer.update(NOW,8).state,'invalid')

    def test_changed_during_read_is_rejected_and_new_generation_can_recover(self):
        self.write();stamp=probe(self.path)
        real=home_refresh.os.fstat;calls=[]
        def changing(fd):
            metadata=real(fd);calls.append(None)
            if len(calls)==2:
                self.write()
            return metadata
        with patch.object(home_refresh.os,'fstat',side_effect=changing):
            self.assertEqual(read_generation(self.path,stamp),{})
        self.assertEqual(self.consumer.update(NOW,0).state,'fresh')

    def test_bad_json_duplicates_utf8_nonfinite_nested_and_cached_invalid(self):
        for i,raw in enumerate((b'{',b'\xff',b'{"a":1,"a":2}',b'{"a":NaN}',b'['*2000,b'null')):
            self.write(raw=raw);self.assertEqual(self.consumer.update(NOW,i*4).state,'invalid')
            reads=self.consumer.reads;self.consumer.update(NOW,i*4+2)
            self.assertEqual(self.consumer.reads,reads)

    def test_same_source_second_can_have_reviewed_changed_values(self):
        self.write();self.consumer.update(NOW,0)
        value=fixture();value['generated_at']=NOW.isoformat();value['snapshot']['lights'][0]['state']='off'
        self.write(value);self.assertEqual(self.consumer.update(NOW,2).state,'fresh')
        self.assertEqual(self.consumer.generations,2)

    def test_future_rejection_does_not_advance_accepted_highwater(self):
        self.write();self.consumer.update(NOW,0);clocks=self.consumer.highwater
        value=fixture();value['source_updated_at']=(NOW+timedelta(seconds=400)).isoformat();self.write(value)
        self.assertEqual(self.consumer.update(NOW,2).state,'future')
        self.assertEqual(self.consumer.highwater,clocks)
        self.write();self.assertEqual(self.consumer.update(NOW,4).state,'fresh')

    def test_bundle_integrity_fixed_fixture_and_no_runtime_network_or_writes(self):
        import hashlib,importlib.util,sys,types
        from build_home_refresh_preview import build
        root=self.root/'bundle';pin=build(root)
        manifest=json.loads((root/'manifest.json').read_text())
        self.assertEqual(len(manifest['files']),6)
        self.assertEqual(hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(),pin)
        spec=importlib.util.spec_from_file_location('refresh_entry',root/'default.py')
        module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,xbmc=types.ModuleType('xbmc'),xbmcgui=types.ModuleType('xbmcgui')):
            spec.loader.exec_module(module)
        module.verify(pin)
        with self.assertRaises(ValueError):module.verify('0'*64)
        path=root/'resources/lib/home_refresh.py';path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaises(ValueError):module.verify(pin)
        with self.assertRaises(FileExistsError):build(root)
        code=(root/'default.py').read_text()
        for banned in ('Player.Open','Player.Stop','urllib','requests','subprocess','os.replace(',
                       'write_text(','write_bytes(','call_service','getControl(136)'):
            self.assertNotIn(banned,code)
        self.assertIn("source=ROOT/'synthetic-home.json' if synthetic else FEED",code)
        self.assertIn('NOT household readings',code)
