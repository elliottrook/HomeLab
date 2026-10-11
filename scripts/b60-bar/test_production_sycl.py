import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('stage_prod',Path(__file__).with_name('stage-production-sycl.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class ProductionTests(unittest.TestCase):
    def test_exact_unit_transform_preserves_model_api_and_inference(self):
        old=Path(__file__).parents[1].joinpath('b60-inference/aster-llama-9b.service').read_text()
        new=s.candidate_unit(old,Path('/opt/aster-sycl-b11429'),'/private/libs')
        before=next(l for l in old.splitlines() if l.startswith('ExecStart=')).split(' -m ',1)[1]
        after=next(l for l in new.splitlines() if l.startswith('ExecStart=')).split(' -m ',1)[1]
        self.assertEqual(after,before+' --log-verbosity 4')
        self.assertIn('Restart=no',new)
        self.assertIn('Environment=GGML_SYCL_ENABLE_FUSION=1',new)
        self.assertNotIn('/dev/shm',new)
        self.assertIn('TimeoutStartSec=330s',new)
    def test_drift_rejected(self):
        with self.assertRaises(AssertionError):s.candidate_unit('unexpected',Path('/opt/test'),'libs')
    def test_escaping_link_rejected_and_content_hash_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a').write_bytes(b'synthetic')
            self.assertEqual(s.tree_manifest(p)['a']['sha256'],s.digest(p/'a'))
            (p/'escape').symlink_to('../outside')
            with self.assertRaises(AssertionError):s.tree_manifest(p)
    def test_create_once(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'proof';s.write_once(p,b'one')
            with self.assertRaises(FileExistsError):s.write_once(p,b'two')
            self.assertEqual(p.read_bytes(),b'one')

if __name__=='__main__':unittest.main()
