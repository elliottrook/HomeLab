import unittest
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import tempfile
import types
from unittest.mock import patch
from youtube_branding import validate, replace_home, OLD, NEW


class YouTubeBrandingTests(unittest.TestCase):
    def test_approved_vector_is_self_contained(self):
        path = Path(__file__).resolve().parents[3] / 'docs/assets/aster-v2/SVG/33-aster-youtube.svg'
        self.assertEqual(validate(path.read_bytes()).get('width'), '1254')

    def test_only_texture_changes(self):
        source = b'<window><control id="136" type="button"><label>YouTube</label><onclick>same</onclick></control><control type="image"><texture>' + OLD + b'</texture><aspectratio>keep</aspectratio></control></window>'
        result = replace_home(source)
        self.assertEqual(result.replace(NEW, OLD), source)

    def test_duplicate_or_missing_original_refused(self):
        for source in (b'<window/>', b'<window>' + OLD + OLD + b'</window>'):
            with self.assertRaises(ValueError): replace_home(source)

    def test_changed_master_refused(self):
        with self.assertRaisesRegex(ValueError, 'master-drift'): validate(b'<svg/>')

    def test_runtime_is_square_128_png(self):
        path = Path(__file__).parent.parent / 'skin.asterhome/media/33-aster-youtube-128.png'
        data = path.read_bytes()
        self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(tuple(int.from_bytes(data[i:i+4], 'big') for i in (16, 20)), (128, 128))


class YouTubeDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        def require(value, code):
            if not value: raise RuntimeError(code)
        self.guard = types.SimpleNamespace(require=require, sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(),
            idle=lambda:True, snapshot=lambda:dict(settings='same', navigation='same'))
        with patch.dict(sys.modules, deploy_startup=self.guard, xbmc=types.SimpleNamespace(executebuiltin=lambda action:None)):
            spec = importlib.util.spec_from_file_location('youtube_deploy_test', Path(__file__).parent / 'tools/deploy_youtube_branding.py')
            self.m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.m)
        self.m.BASE = root / 'stage'
        self.m.BASE.mkdir()
        self.m.CHECKPOINT = root / 'checkpoint'
        self.m.SKIN = root / 'skin'
        self.m.ICON = root / 'youtube-icon.png'
        self.m.ICON.write_bytes(b'synthetic-original-icon')
        (self.m.SKIN / '1080i').mkdir(parents=True)
        (self.m.SKIN / 'media').mkdir()
        self.before = b'<window><control id="136"><label>YouTube</label></control><control><texture>' + OLD + b'</texture></control></window>'
        (self.m.SKIN / '1080i/Home.xml').write_bytes(self.before)
        (self.m.BASE / '33-aster-youtube-128.png').write_bytes(b'synthetic-png')
        (self.m.BASE / '33-aster-youtube-512.png').write_bytes(b'synthetic-large-png')
        manifest = dict(home_sha256=hashlib.sha256(self.before).hexdigest(),
            original_icon_sha256=self.guard.sha(self.m.ICON), files={
            name:self.guard.sha(self.m.BASE / name) for name in ('33-aster-youtube-128.png', '33-aster-youtube-512.png')})
        (self.m.BASE / 'manifest.json').write_text(json.dumps(manifest))
        self.m.MANIFEST = self.guard.sha(self.m.BASE / 'manifest.json')
        for name in ('deploy_youtube_branding.py', 'deploy_startup.py', 'youtube_branding.py'):
            (self.m.BASE / name).write_text('synthetic paired recovery fixture')
        guard = patch.object(self.m.os, 'uname', return_value=types.SimpleNamespace(nodename='AsterTV'))
        guard.start()
        self.addCleanup(guard.stop)

    def test_exact_install_verify_and_retained_rollback(self):
        self.assertTrue(self.m.main('deploy')['passed'])
        self.assertTrue(self.m.main('verify')['passed'])
        self.assertTrue(self.m.main('rollback')['passed'])
        self.assertEqual((self.m.SKIN / '1080i/Home.xml').read_bytes(), self.before)
        self.assertEqual(self.m.ICON.read_bytes(), b'synthetic-original-icon')
        self.assertTrue((self.m.CHECKPOINT / 'disabled-33-aster-youtube-128.png').exists())

    def test_production_refused(self):
        with patch.object(self.m.os, 'uname', return_value=types.SimpleNamespace(nodename='AsterTVProd')):
            with self.assertRaisesRegex(RuntimeError, 'hp-only'): self.m.main('deploy')
        self.assertFalse(self.m.CHECKPOINT.exists())

    def test_busy_refused(self):
        self.guard.idle = lambda:False
        with self.assertRaisesRegex(RuntimeError, 'idle-empty'): self.m.main('deploy')
        self.assertFalse(self.m.CHECKPOINT.exists())

    def test_unexpected_home_refused(self):
        (self.m.SKIN / '1080i/Home.xml').write_text('newer-user-change')
        with self.assertRaisesRegex(RuntimeError, 'home-must-be-unchanged'): self.m.main('deploy')
        self.assertFalse(self.m.CHECKPOINT.exists())


if __name__ == '__main__': unittest.main()
