from dataclasses import replace
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from build_digest_news import build, patch_handler
from build_digest_player import build as player_bundle
from digest_news_contract import request, row_for
from digest_news_install import run, inspect, verify, accepted_overrides, HUB, SHIM, BEFORE, CHECKPOINT, PLAYER, PLAYER_PIN
sys.path.insert(0, str(Path(__file__).parent.parent/'skin.asterhome/tools'))
from digest_preview_model import load


class DigestNewsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.storage = self.root/'storage'
        self.stage = self.storage/'.aster-staging/aster-digest-news1'
        self.stage.parent.mkdir(parents=True)
        self.pin = build(self.stage)
        player = self.storage/'.aster-staging'/PLAYER
        self.assertEqual(player_bundle(player), PLAYER_PIN)
        target = self.storage/HUB
        target.parent.mkdir(parents=True)
        shutil.copyfile(Path(__file__).parent.parent/'skin.asterhome/tools/hub_data.py', target)
        now = datetime(2026, 10, 25, 20, tzinfo=timezone.utc)
        self.stamp = now.isoformat()
        feed = dict(digest_run='synthetic', generated_at=self.stamp, duration_seconds=120,
            story_count=2, chapters=[dict(index=1, title='First', start=10), dict(index=2, title='Second', start=60)])
        self.snapshot = load(lambda path, limit:json.dumps(feed).encode() if path.endswith('.json') else b'', now)

    def test_explicit_request_context_and_matching_story(self):
        self.assertIsNone(request([], 10000))
        full = request(['news', 'full', '0', self.stamp], 11111)
        self.assertEqual(row_for(full, self.snapshot), 0)
        story = request(['news', 'story', '60', self.stamp], 11111)
        self.assertEqual(row_for(story, self.snapshot), 2)
        with self.assertRaises(ValueError): row_for(dict(story, generation='other'), self.snapshot)
        with self.assertRaises(ValueError): row_for(dict(story, position=15), self.snapshot)

    def test_native_row_selection_waits_for_exact_target_not_just_focus(self):
        source=(Path(__file__).parent/'tools/live_digest_news.py').read_text()
        node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='selected_position')
        values=iter(('', '4.0', '50.0'))
        scope={'xbmc':types.SimpleNamespace(getInfoLabel=lambda _:next(values))}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<native-selection-test>','exec'),scope)
        self.assertIsNone(scope['selected_position']())
        self.assertNotEqual(scope['selected_position'](),50.0)
        self.assertEqual(scope['selected_position'](),50.0)
        self.assertIn('focus(500) and selected_position() == position',source)

    def test_invalid_handoff_never_becomes_a_command(self):
        for args, source in (([], 11111), (['news','full','0',self.stamp],10000),
                (['news','full','10',self.stamp],11111), (['news','story','nan',self.stamp],11111),
                (['news','story','-1',self.stamp],11111), (['news','story','1,Stop',self.stamp],11111),
                (['news','full','0','2026-10-25T20:00:00'],11111),
                (['news','full','0',self.stamp+',x'],11111)):
            with self.assertRaises(ValueError): request(args, source)

    def test_patch_changes_only_digest_play_and_chapter(self):
        original = (self.storage/HUB).read_bytes()
        patched = patch_handler(original)
        block = b"    if page == 'digest' and action in ('play', 'chapter'):\n        from aster_v2_digest import main as open_digest_player\n        open_digest_player(action)\n        return\n"
        self.assertEqual(patched.count(block), 1)
        self.assertEqual(patched.replace(block,b''), original)
        with self.assertRaises(ValueError): patch_handler(original+b'\n')

    def test_install_verify_rollback_reinstall_is_exact(self):
        self.assertTrue(run('install', self.stage, self.storage, self.pin, idle=lambda:True)['installed'])
        self.assertTrue(run('verify', self.stage, self.storage, self.pin, idle=lambda:True)['verified'])
        self.assertEqual(set(accepted_overrides(self.stage,self.storage,self.pin)),
            {HUB[len('.kodi/addons/'):],SHIM[len('.kodi/addons/'):]})
        self.assertTrue(run('rollback', self.stage, self.storage, self.pin, idle=lambda:True)['original_restored'])
        self.assertEqual(hashlib.sha256((self.storage/HUB).read_bytes()).hexdigest(), BEFORE)
        self.assertTrue((self.storage/SHIM).exists())
        self.assertEqual(accepted_overrides(self.stage,self.storage,self.pin), {})
        self.assertEqual(verify(self.stage, self.storage, self.pin, restored=True)['kind'], 'hp-digest-news.v1')
        self.assertTrue(run('install', self.stage, self.storage, self.pin, idle=lambda:True)['installed'])

    def test_busy_or_unknown_predecessor_denied(self):
        with self.assertRaisesRegex(ValueError,'idle'): run('install',self.stage,self.storage,self.pin,idle=lambda:False)
        self.assertFalse((self.storage/CHECKPOINT).exists())
        (self.storage/HUB).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'predecessor'): run('install',self.stage,self.storage,self.pin,idle=lambda:True)

    def test_stage_player_and_backup_drift_denied(self):
        player = self.storage/'.aster-staging'/PLAYER/'default.py'
        original = player.read_bytes()
        player.write_bytes(original+b'\n')
        with self.assertRaisesRegex(ValueError,'player-member'): inspect(self.stage,self.storage,self.pin)
        player.write_bytes(original)
        run('install',self.stage,self.storage,self.pin,idle=lambda:True)
        (self.storage/CHECKPOINT/'hub_data.py').write_bytes(b'bad backup')
        with self.assertRaisesRegex(ValueError,'recovery'): run('rollback',self.stage,self.storage,self.pin,idle=lambda:True)

    def test_unknown_shim_and_symlink_denied(self):
        (self.storage/SHIM).write_bytes(b'existing')
        with self.assertRaisesRegex(ValueError,'unknown-shim'): run('install',self.stage,self.storage,self.pin,idle=lambda:True)
        (self.storage/SHIM).unlink()
        (self.storage/SHIM).symlink_to(self.storage/HUB)
        with self.assertRaisesRegex(ValueError,'linked'): inspect(self.stage,self.storage,self.pin)

    def test_bundle_is_immutable(self):
        with self.assertRaisesRegex(ValueError,'immutable'): build(self.stage)

    def shim_trial(self, action, *, leave_during_cache=False):
        spec = importlib.util.spec_from_file_location('isolated_news_shim', Path(__file__).parent/'tools/aster_v2_digest.py')
        shim = importlib.util.module_from_spec(spec); spec.loader.exec_module(shim)
        shim.PLAYER = self.storage/'.aster-staging'/PLAYER
        generation = datetime.now(timezone.utc).isoformat()
        feed = dict(digest_run='synthetic', generated_at=generation, duration_seconds=120,
            story_count=1, chapters=[dict(index=1,title='Test',start=10)])
        env = dict(page=11111, commands=[], caches=[], notices=[], properties={})
        window = types.SimpleNamespace(getFocusId=lambda:305,
            getProperty=lambda key:{'AsterHub.Ready':'true','AsterHub.GeneratedAt':generation}.get(key,''),
            setProperty=lambda key,value:env['properties'].update({key:value}))
        def cache(*args):
            env['caches'].append(True)
            if leave_during_cache: env['page'] = 10000
        modules = dict(xbmc=types.SimpleNamespace(executebuiltin=lambda value:env['commands'].append(value),
                getInfoLabel=lambda key:'10'),
            xbmcgui=types.SimpleNamespace(Window=lambda _:window, getCurrentWindowId=lambda:env['page'],
                Dialog=lambda:types.SimpleNamespace(notification=lambda *args:env['notices'].append(args))),
            xbmcvfs=types.SimpleNamespace(), digest_kodi_port=types.SimpleNamespace(idle=lambda:True),
            digest_preview_source=types.SimpleNamespace(read=lambda *args:json.dumps(feed).encode()),
            hub_data=types.SimpleNamespace(cached_digest_audio=cache))
        with patch.dict(sys.modules, modules), patch('os.uname', return_value=types.SimpleNamespace(nodename='AsterTV')):
            shim.main(action)
        return env

    def test_handoff_caches_only_on_explicit_play(self):
        env = self.shim_trial('play')
        self.assertEqual(len(env['caches']), 1)
        self.assertEqual(len(env['commands']), 1)
        self.assertIn(',news,full,0,', env['commands'][0])
        self.assertEqual(env['notices'], [])
        passive = self.shim_trial('refresh')
        self.assertEqual(passive['caches'], [])
        self.assertEqual(passive['commands'], [])

    def test_navigation_during_cache_never_launches_player(self):
        env = self.shim_trial('play', leave_during_cache=True)
        self.assertEqual(env['commands'], [])
        self.assertEqual(env['properties'], {})
        self.assertEqual(len(env['notices']), 1)

    def test_story_handoff_keeps_return_context(self):
        env = self.shim_trial('chapter')
        self.assertEqual(len(env['commands']), 1)
        self.assertIn(',news,story,10,', env['commands'][0])
        self.assertEqual(env['properties']['AsterHub.RequestedStart'], '10')


if __name__ == '__main__': unittest.main()
