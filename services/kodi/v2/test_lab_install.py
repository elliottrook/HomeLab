import importlib.util,json,tempfile,unittest
from pathlib import Path
from build_lab import build

spec=importlib.util.spec_from_file_location('lab_installer',Path(__file__).parent/'tools/install_lab_candidate.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)

class InstallTests(unittest.TestCase):
    def test_checks_fail_closed_under_optimized_python(self):
        with self.assertRaisesRegex(RuntimeError,'denied'):installer.require(False,'denied')
    def test_exact_built_candidate_hash_and_members_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            stage=Path(folder);manifest=build(stage)
            self.assertEqual(installer.verify(stage,manifest['sha256']),manifest)
            with self.assertRaises(RuntimeError):installer.verify(stage,'0'*64)
    def test_manifest_path_and_archive_tampering_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            stage=Path(folder);manifest=build(stage);path=stage/'manifest.json'
            manifest['files'][0]['path']='../escape'
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(RuntimeError,'unsafe-member'):installer.verify(stage,manifest['sha256'])
            clean=stage/'clean';manifest=build(clean)
            archive=clean/manifest['archive'];archive.write_bytes(archive.read_bytes()+b'tampered')
            with self.assertRaisesRegex(RuntimeError,'archive-hash'):installer.verify(clean,manifest['sha256'])
