import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('private_move',Path(__file__).with_name('move-private-runtime-to-tmpfs.py'))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PrivateMoveTests(unittest.TestCase):
    def test_move_preserves_bytes_modes_and_namespace(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=root/'disk'/'root'
            source.mkdir(parents=True)
            (source/'private.so.1').write_bytes(b'synthetic private library')
            (source/'private.so').symlink_to('private.so.1')
            original=module.manifest(source)
            dest=root/'ram'/'root'
            calls=[]
            def run(command,**kwargs):
                calls.append(command)
                if command[0]=='mv':
                    shutil.move(command[2],command[3])
                    return subprocess.CompletedProcess(command,0)
                return subprocess.CompletedProcess(command,3,'inactive','')
            with patch.object(module,'SOURCE',source),patch.object(module,'DEST',dest), \
                 patch.object(module.subprocess,'run',side_effect=run), \
                 patch.object(module.subprocess,'check_output',return_value='active'), \
                 patch.object(module.shutil,'disk_usage',return_value=SimpleNamespace(free=30*1024**3)), \
                 patch.object(Path,'read_text',return_value='MemAvailable: 16777216 kB'):
                module.main()
            self.assertTrue(source.is_symlink())
            self.assertEqual(module.manifest(dest),original)
            self.assertEqual((source/'private.so').read_bytes(),b'synthetic private library')
            proof=json.loads((dest.parent/'migration-proof.json').read_text())
            self.assertFalse(proof['accepted_production_changed'])
            self.assertEqual([c for c in calls if c[0]=='mv'],[['mv','--',str(source),str(dest)]])

    def test_candidate_active_refuses_storage_change(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'root'
            source.mkdir()
            dest=Path(directory)/'ram'/'root'
            with patch.object(module,'SOURCE',source),patch.object(module,'DEST',dest), \
                 patch.object(module.subprocess,'check_output',return_value='active'), \
                 patch.object(module.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'active','')) as run:
                with self.assertRaises(AssertionError): module.main()
                self.assertEqual(run.call_count,1)
            self.assertFalse(dest.exists())
