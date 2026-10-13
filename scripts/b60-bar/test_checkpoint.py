import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('verify_checkpoint',Path(__file__).with_name('verify-checkpoint.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
POPEN=subprocess.Popen
class CheckpointTests(unittest.TestCase):
 def test_single_pass_digest_and_exact_files(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);archive=root/'archive';proof=root/'proof'
   with tarfile.open(archive,'w') as t:
    raw=b'synthetic accepted artifact';m=tarfile.TarInfo('./exact');m.size=len(raw);t.addfile(m,io.BytesIO(raw))
   expected={'exact':hashlib.sha256(raw).hexdigest()}
   def pipe(*args,**kwargs):return POPEN([sys.executable,'-c','import sys,shutil;shutil.copyfileobj(sys.stdin.buffer,sys.stdout.buffer)'],**kwargs)
   with patch.object(s,'ARCHIVE',archive),patch.object(s,'PROOF',proof),patch.object(s,'EXPECTED',expected),patch.object(s.subprocess,'Popen',side_effect=pipe):
    s.main()
    record=json.loads(proof.read_text())
    self.assertEqual(record['sha256'],hashlib.sha256(archive.read_bytes()).hexdigest())
    self.assertEqual(record['accepted_files_verified'],expected)
    self.assertTrue(record['compressed_integrity_passed'])
    with self.assertRaises(FileExistsError):s.main()
 def test_missing_accepted_file_refuses_proof(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);archive=root/'archive';proof=root/'proof'
   with tarfile.open(archive,'w'):pass
   def pipe(*args,**kwargs):return POPEN([sys.executable,'-c','import sys,shutil;shutil.copyfileobj(sys.stdin.buffer,sys.stdout.buffer)'],**kwargs)
   with patch.object(s,'ARCHIVE',archive),patch.object(s,'PROOF',proof),patch.object(s,'EXPECTED',{'missing':'0'*64}),patch.object(s.subprocess,'Popen',side_effect=pipe):
    with self.assertRaises(AssertionError):s.main()
    self.assertFalse(proof.exists())
if __name__=='__main__':unittest.main()
