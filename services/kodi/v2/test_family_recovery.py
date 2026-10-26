import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build_family_recovery import build
from family_runtime import COMPONENTS, SKIN_LAUNCHERS


def digest(raw): return hashlib.sha256(raw).hexdigest()
def put(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
def encoded(value): return json.dumps(value, sort_keys=True).encode()+b'\n'


class FamilyRecoveryTests(unittest.TestCase):
    def fixture(self, root):
        addon=root/'addon'; skin=root/'skin'; checkpoint=root/'checkpoint'; guard=root/'guard'
        put(addon/'addon.xml', b'<addon/>'); put(addon/'default.py', b'pass\n')
        put(addon/'music72-manifest.json', b'{"music":72}\n')
        put(addon/'shared/runtime_guard.py', b'def ready(): return True\n')
        components={}
        for name in COMPONENTS:
            raw=('payload-'+name).encode(); put(addon/name/'default.py', raw)
            manifest=encoded(dict(schema=1, component=name,
                files=[dict(path='default.py',bytes=len(raw),sha256=digest(raw))]))
            put(addon/name/'manifest.json', manifest)
            components[name]=dict(manifest_sha256=digest(manifest),files=1)
        skin_hashes={}; old=[]
        for index,relative in enumerate(SKIN_LAUNCHERS):
            before=('before-'+relative).encode(); current=('current-'+relative).encode()
            put(checkpoint/'original'/relative,before); put(skin/relative,current)
            old.append(dict(path=relative,before_sha256=digest(before),sha256='0'*64))
            skin_hashes[relative]=digest(current)
        for relative in ('1080i/custom_1127_search.xml','1080i/custom_1128_searchdetails.xml',
                         '1080i/custom_1129_artistalbums.xml','tools/select_dispatch.py'):
            raw=('current-'+relative).encode(); put(skin/relative,raw); skin_hashes[relative]=digest(raw)
        family=dict(schema=1,kind='aster-family-runtime.v1',components=components,
            music_manifest_sha256=digest((addon/'music72-manifest.json').read_bytes()),
            shared=dict(runtime_guard_sha256=digest((addon/'shared/runtime_guard.py').read_bytes())),
            skin=skin_hashes)
        put(addon/'family-manifest.json',encoded(family))
        put(checkpoint/'manifest.json',encoded(dict(kind='hp-family-release-candidate.v1',skin=old)))
        put(checkpoint/'state.json',b'{"state":"installed"}\n')
        before=b'old-player'; active=b'guarded-player'; player=root/'player.py'; put(player,active)
        put(guard/'manifest.json',encoded(dict(kind='hp-jellyfin-idle-guard.v1',
            before_sha256=digest(before),sha256=digest(active))))
        put(guard/'state.json',b'{"state":"installed"}\n'); put(guard/'player.py.before',before)
        return addon,skin,checkpoint,player,guard

    def test_build_is_clean_exact_and_deterministic(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent); args=self.fixture(root)
            one=root/'one'; two=root/'two'
            self.assertEqual(build(*args,one),build(*args,two))
            self.assertEqual((one/'manifest.json').read_bytes(),(two/'manifest.json').read_bytes())
            manifest=json.loads((one/'manifest.json').read_text())
            self.assertEqual(manifest['kind'],'aster-family-recovery.v1')
            self.assertEqual(len(manifest['skin']),8)
            self.assertEqual(len(manifest['external']),1)
            self.assertFalse(any('__pycache__' in row['path'] for row in manifest['addon_files']))

    def test_drift_and_existing_output_are_refused(self):
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent); args=self.fixture(root)
            (args[1]/SKIN_LAUNCHERS[0]).write_bytes(b'drift')
            with self.assertRaisesRegex(ValueError,'skin-drift'): build(*args,root/'out')
        with tempfile.TemporaryDirectory() as parent:
            root=Path(parent); args=self.fixture(root); out=root/'out'; out.mkdir()
            with self.assertRaisesRegex(ValueError,'output-exists'): build(*args,out)


if __name__ == '__main__': unittest.main()
