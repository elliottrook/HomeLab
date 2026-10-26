from datetime import timedelta
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import home_publication as publication
from test_home_freshness import NOW
from test_home_preview import fixture


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.feed=self.root/'home.json';self.cp=self.root/'checkpoint'
        self.original=b'{"synthetic-old-feed":true}\n'
        self.feed.write_bytes(self.original);self.feed.chmod(0o600)
        os.utime(self.feed,ns=(1700000000000000000,1700000000000000001))
        self.time=self.feed.stat().st_mtime_ns
        self.candidate=json.dumps(fixture()).encode()
        self.oldsha=publication.digest(self.original);self.newsha=publication.digest(self.candidate)

    def checkpoint(self):return publication.checkpoint(self.feed,self.cp,self.oldsha)
    def apply(self,ready=lambda:True,clock=lambda:NOW):
        publication.apply(self.feed,self.cp,self.candidate,self.newsha,ready,clock)

    def test_backup_isolated_restore_apply_and_exact_rollback(self):
        self.checkpoint()
        self.assertEqual(publication.read_private(self.cp/'before.bin')[0],self.original)
        self.assertEqual((self.cp/'isolated-restore.bin').stat().st_mtime_ns,self.time)
        self.apply();self.assertEqual(self.feed.read_bytes(),self.candidate)
        self.assertEqual(self.feed.stat().st_mode&0o777,0o600)
        publication.restore(self.feed,self.cp)
        self.assertEqual(self.feed.read_bytes(),self.original)
        self.assertEqual(self.feed.stat().st_mtime_ns,self.time)
        self.assertEqual(publication.load_state(self.cp)['phase'],'restored')
        self.assertEqual(self.cp.stat().st_mode&0o777,0o700)
        with self.assertRaisesRegex(ValueError,'one-use-only'):self.apply()

    def test_refuse_unknown_before_or_reused_checkpoint(self):
        with self.assertRaisesRegex(ValueError,'before-drift'):
            publication.checkpoint(self.feed,self.cp,'0'*64)
        self.assertFalse(self.cp.exists());self.checkpoint()
        with self.assertRaises(FileExistsError):self.checkpoint()
        self.assertEqual(self.feed.read_bytes(),self.original)

    def test_refuse_links_hardlinks_public_files_and_oversize(self):
        self.feed.chmod(0o644)
        with self.assertRaisesRegex(ValueError,'private-file'):publication.read_private(self.feed)
        self.feed.chmod(0o600);link=self.root/'linked';link.symlink_to(self.feed)
        with self.assertRaisesRegex(ValueError,'linked'):publication.read_private(link)
        hard=self.root/'hard';os.link(self.feed,hard)
        with self.assertRaisesRegex(ValueError,'private-file'):publication.read_private(self.feed)
        hard.unlink();self.feed.write_bytes(b'x'*262145)
        with self.assertRaisesRegex(ValueError,'private-file'):publication.read_private(self.feed)

    def test_refuse_invalid_stale_future_or_camera_candidate_without_write(self):
        self.checkpoint()
        for value in (b'{}', b'null', b'{"a":1,"a":2}', b'\xff'):
            with self.assertRaises(ValueError):
                publication.apply(self.feed,self.cp,value,publication.digest(value),lambda:True,lambda:NOW)
        for delta in (timedelta(seconds=601),timedelta(seconds=-303)):
            with self.assertRaises(ValueError):self.apply(clock=lambda:NOW+delta)
        value=fixture();value['snapshot']['cameras']=[];raw=json.dumps(value).encode()
        with self.assertRaisesRegex(ValueError,'source-contract'):
            publication.apply(self.feed,self.cp,raw,publication.digest(raw),lambda:True,lambda:NOW)
        self.assertEqual(self.feed.read_bytes(),self.original)
        self.assertEqual(publication.load_state(self.cp)['phase'],'prepared')

    def test_idle_guard_rechecked_after_temporary_write(self):
        self.checkpoint();calls=iter([True,False])
        with self.assertRaisesRegex(ValueError,'not-idle'):self.apply(ready=lambda:next(calls))
        self.assertEqual(self.feed.read_bytes(),self.original)
        self.assertEqual(list(self.root.glob('.home-trial-*')),[])
        publication.restore(self.feed,self.cp)
        self.assertEqual(publication.load_state(self.cp)['phase'],'restored')

    def test_expiry_during_preparation_refuses_atomic_replace(self):
        self.checkpoint();clocks=iter([NOW,NOW+timedelta(seconds=601)])
        with self.assertRaisesRegex(ValueError,'stale'):self.apply(clock=lambda:next(clocks))
        self.assertEqual(self.feed.read_bytes(),self.original)
        publication.restore(self.feed,self.cp)

    def test_foreign_write_is_never_overwritten_by_apply_or_rollback(self):
        self.checkpoint();self.feed.write_bytes(b'foreign')
        with self.assertRaisesRegex(ValueError,'foreign-write'):self.apply()
        with self.assertRaisesRegex(ValueError,'foreign-write'):publication.restore(self.feed,self.cp)
        self.assertEqual(self.feed.read_bytes(),b'foreign')

    def test_interrupted_pending_apply_can_be_restored_not_retried(self):
        self.checkpoint()
        real=publication.save_state
        def save(folder,state):
            if state['phase']=='applied':raise OSError('synthetic-interrupted-state-write')
            return real(folder,state)
        with patch.object(publication,'save_state',side_effect=save):
            with self.assertRaises(OSError):self.apply()
        self.assertEqual(self.feed.read_bytes(),self.candidate)
        self.assertEqual(publication.load_state(self.cp)['phase'],'apply-pending')
        with self.assertRaisesRegex(ValueError,'one-use-only'):self.apply()
        publication.restore(self.feed,self.cp)
        self.assertEqual(self.feed.read_bytes(),self.original)

    def test_corrupt_backup_never_restores_over_candidate(self):
        self.checkpoint();self.apply();(self.cp/'before.bin').write_bytes(b'bad-backup')
        with self.assertRaisesRegex(ValueError,'backup-drift'):publication.restore(self.feed,self.cp)
        self.assertEqual(self.feed.read_bytes(),self.candidate)

    def test_existing_home_reader_accepts_reviewed_candidate(self):
        import importlib.util
        source=Path(__file__).parent.parent/'skin.asterhome/tools/hub_feeds.py'
        spec=importlib.util.spec_from_file_location('home_publication_legacy',source)
        legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
        with patch.object(legacy,'_fresh',lambda *_:None):
            values=legacy.home_dashboard(fixture())
        self.assertEqual(values['LightValue'],'On')
        self.assertEqual(values['CameraStatus'],'No reviewed camera')
        self.assertEqual(values['TimerLabel'],'Not connected')

    def test_trial_bundle_is_private_pinned_one_shot_and_no_auto_refresh(self):
        from build_home_feed_trial import build,MEMBERS
        root=self.root/'bundle';pin=build(root)
        manifest=json.loads((root/'manifest.json').read_text())
        self.assertEqual(publication.digest((root/'manifest.json').read_bytes()),pin)
        self.assertEqual({r['path'] for r in manifest['files']},MEMBERS)
        self.assertTrue(manifest['one_shot']);self.assertTrue(manifest['restore_original'])
        self.assertFalse(manifest['automatic_refresh']);self.assertFalse(manifest['production'])
        self.assertEqual(root.stat().st_mode&0o777,0o700)
        for row in manifest['files']:
            path=root/row['path'];self.assertEqual(path.stat().st_mode&0o777,0o600)
            self.assertEqual(publication.digest(path.read_bytes()),row['sha256'])
        with self.assertRaises(FileExistsError):build(root)
        script=(root/'live_home_feed_trial.py').read_text()
        for forbidden in ('assert ', 'Player.Open','Player.Stop','urllib','requests','TakeScreenshot','setProperty('):
            self.assertNotIn(forbidden,script)
        self.assertIn('publication.restore(FEED,CHECKPOINT)',script)
        self.assertIn('home-trial-already-consumed',script)
