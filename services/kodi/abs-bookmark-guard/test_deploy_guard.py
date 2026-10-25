"""Synthetic activation-plan checks; never invokes the real Docker service."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
YAML_AVAILABLE=importlib.util.find_spec('yaml') is not None
if YAML_AVAILABLE:import deploy_guard as deploy

@unittest.skipUnless(YAML_AVAILABLE,'Run these five tests with TrueNAS PyYAML; no local dependency installation')
class DeploymentPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'manifest.json').write_text(json.dumps(dict(files=[
            dict(path=p) for p in ('server/models/User.js','server/controllers/MeController.js','server/routers/ApiRouter.js',
                                 'server/libs/asterBookmarkGuard.js','server/libs/asterBookmarkController.js')])))
        p=patch.object(deploy,'STAGE',self.root);p.start();self.addCleanup(p.stop)
        self.source=b'''services:
  audiobookshelf:
    image: pinned-image
    ports: ["192.168.20.40:30067:80"]
    volumes:
      - /mnt/Media/audiobooks:/audiobooks:rw
      - /mnt/Media/podcasts:/podcasts:rw
    restart: unless-stopped
  unrelated:
    image: unchanged
    environment: ["PRIVATE=synthetic-only"]
networks:
  default:
    name: existing-network
'''
    def test_only_five_readonly_code_mounts_added(self):
        changed=deploy.yaml.safe_load(deploy.patch_compose(self.source));old=deploy.yaml.safe_load(self.source)
        mounts=changed['services']['audiobookshelf']['volumes'];self.assertEqual(len(mounts),7)
        self.assertTrue(all(m.endswith(':ro') and ':/app/server/' in m for m in mounts[-5:]))
        changed['services']['audiobookshelf']['volumes']=mounts[:-5];self.assertEqual(changed,old)
    def test_root_networks_stay_outside_service(self):
        data=deploy.patch_compose(self.source)
        self.assertEqual(deploy.yaml.safe_load(data)['networks'],deploy.yaml.safe_load(self.source)['networks'])
        self.assertIn(b'  unrelated:\n    image: unchanged',data)
    def test_missing_volume_anchor_refuses(self):
        with self.assertRaisesRegex(RuntimeError,'volume-text-anchor'):
            deploy.patch_compose(self.source.replace(b'    volumes:',b'    notvolumes:'))
    def test_backup_proof_cannot_mount_live_config(self):
        with patch.object(deploy,'command') as command:
            with self.assertRaisesRegex(RuntimeError,'isolated-backup-only'):deploy.coherent(deploy.CONFIG/'absdatabase.sqlite')
            command.assert_not_called()
    def test_backup_proof_is_offline_readonly_and_pinned(self):
        path=deploy.CHECKPOINT/'isolated-restore/absdatabase.sqlite'
        with patch.object(deploy,'command',return_value=b'{"ok":true,"tables":28}') as command:
            self.assertEqual(deploy.coherent(path),28)
        args=command.call_args.args[0]
        self.assertIn(deploy.IMAGE_ID,args);self.assertIn('--read-only',args)
        self.assertEqual(args[args.index('--network')+1],'none')
        self.assertTrue(any('dst=/proof,readonly' in a for a in args))
