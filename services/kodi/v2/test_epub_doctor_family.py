import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from build_epub_doctor_family import build
from epub_doctor_family_install import run


def sha(raw): return hashlib.sha256(raw).hexdigest()
def put(path, raw): path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
def encoded(value): return json.dumps(value, sort_keys=True).encode() + b'\n'


class EpubDoctorFamilyTests(unittest.TestCase):
    def fixture(self, root):
        addon, skin, source = root/'addon', root/'skin', root/'source'
        old = 'aster-network-preview5'; new = 'aster-network-preview6'
        old_file = b'old-network'; put(addon/old/'default.py', old_file)
        old_manifest = encoded({'schema': 1, 'component': old,
            'files': [{'path': 'default.py', 'bytes': len(old_file), 'sha256': sha(old_file)}]})
        put(addon/old/'manifest.json', old_manifest)
        dispatcher = ('COMPONENTS={"%s"}\n' % old).encode(); put(addon/'default.py', dispatcher)
        settings = ('RunScript(script.asterruntime,%s,default,%s,diagnostics)' %
                    (old, sha(old_manifest))).encode()
        put(skin/'1080i/Settings.xml', settings)
        family = {'schema': 1, 'kind': 'aster-family-runtime.v1',
                  'components': {old: {'manifest_sha256': sha(old_manifest), 'files': 1}},
                  'skin': {'1080i/Settings.xml': sha(settings)}}
        put(addon/'family-manifest.json', encoded(family))
        new_file = b'import deploy_startup as guard\nPATH="/storage/.aster-staging/x"\n'
        doctor = b"READER = Path('/storage/.aster-staging/aster-books-compiler-reader-v1')\n"
        put(source/'default.py', new_file)
        put(source/'epub_reader_doctor.py', doctor)
        source_manifest = {'kind': 'hp-network-preview.v6', 'books_doctor': True,
                           'repairs': False, 'files': [
            {'path': 'default.py', 'bytes': len(new_file), 'sha256': sha(new_file)},
            {'path': 'epub_reader_doctor.py', 'bytes': len(doctor), 'sha256': sha(doctor)}]}
        put(source/'manifest.json', encoded(source_manifest))
        return addon, skin, source

    def test_build_install_verify_and_rollback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); addon, skin, source = self.fixture(root)
            storage = root/'storage'
            put(storage/'.kodi/addons/script.asterruntime/default.py',
                (addon/'default.py').read_bytes())
            put(storage/'.kodi/addons/script.asterruntime/family-manifest.json',
                (addon/'family-manifest.json').read_bytes())
            put(storage/'.kodi/addons/script.asterruntime/aster-network-preview5/default.py',
                (addon/'aster-network-preview5/default.py').read_bytes())
            put(storage/'.kodi/addons/script.asterruntime/aster-network-preview5/manifest.json',
                (addon/'aster-network-preview5/manifest.json').read_bytes())
            put(storage/'.kodi/addons/skin.asterhome/1080i/Settings.xml',
                (skin/'1080i/Settings.xml').read_bytes())
            bundle = root/'bundle'; pin = build(addon, skin, source, bundle)
            result = run('install', bundle, storage, pin, idle=lambda: True)
            self.assertTrue(result['installed']); self.assertFalse(result['repairs'])
            self.assertTrue(run('verify', bundle, storage, pin,
                                idle=lambda: True)['active'])
            self.assertTrue(run('rollback', bundle, storage, pin,
                                idle=lambda: True)['original_restored'])
            self.assertFalse(run('verify', bundle, storage, pin,
                                 idle=lambda: True)['active'])

    def test_drift_and_busy_client_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); addon, skin, source = self.fixture(root)
            bundle = root/'bundle'; pin = build(addon, skin, source, bundle)
            with self.assertRaisesRegex(ValueError, 'idle'):
                run('install', bundle, root/'missing', pin, idle=lambda: False)
            (bundle/'payload/runtime/default.py').write_bytes(b'drift')
            with self.assertRaisesRegex(ValueError, 'payload-drift'):
                run('install', bundle, root/'missing', pin, idle=lambda: True)


if __name__ == '__main__': unittest.main()
