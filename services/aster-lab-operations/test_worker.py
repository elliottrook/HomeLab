import hashlib
import io
import json
import os
import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from worker import Worker, REQUIRED, verify_config, verify_archive, write_json, run
from guest_helper import validate


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_valid_opnsense_then_corruption(self):
        p = self.root/'opnsense-config-2026.xml'
        p.write_text('<opnsense><version>test</version></opnsense>')
        p.with_suffix('.xml.sha256').write_text(hashlib.sha256(p.read_bytes()).hexdigest()+'  ignored.xml')
        self.assertGreater(verify_config('opnsense', self.root, time.time()), 0)
        p.write_text('<opnsense>corrupted</opnsense>')
        with self.assertRaises(ValueError): verify_config('opnsense', self.root, time.time())

    def test_missing_stale_and_symlink_fail(self):
        d = self.root/'dated'
        d.mkdir()
        for name in REQUIRED['arista']: (d/name).write_text('synthetic fixture')
        self.assertGreater(verify_config('arista', self.root, time.time()), 0)
        path = d/'running-config.txt'
        os.utime(path, (1,1))
        with self.assertRaises(ValueError): verify_config('arista', self.root, time.time())
        path.unlink()
        path.symlink_to(d/'startup-config.txt')
        with self.assertRaises(ValueError): verify_config('arista', self.root, time.time())

    def test_archive_missing_entry_and_truncation(self):
        p=self.root/'fixture.tar.gz'
        with tarfile.open(p, 'w:gz') as archive:
            info=tarfile.TarInfo('etc/test'); info.size=4
            archive.addfile(info, io.BytesIO(b'test'))
        verify_archive(p, ['etc/test'])
        with self.assertRaises(ValueError): verify_archive(p, ['missing'])
        p.write_bytes(p.read_bytes()[:20])
        with self.assertRaises((tarfile.TarError, EOFError)): verify_archive(p, ['etc/test'])

    def test_timeout_is_unknown_not_success(self):
        self.assertIsNone(run(['/bin/sleep','2'], self.root/'log', .01))

    def test_helper_input_cannot_change_command(self):
        self.assertEqual(validate({'target':'guest-104','id':'a'*32})['target'], 'guest-104')
        for value in ({'target':'guest-110','id':'a'*32}, {'target':'guest-104','id':'../../x'},
                      {'target':'guest-104','id':'a'*32,'command':'rm'}, []):
            with self.assertRaises((ValueError, TypeError)): validate(value)


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        snapshot = patch("worker.snapshot_custody", return_value=100)
        snapshot.start(); self.addCleanup(snapshot.stop)
        (self.root/'repo/scripts').mkdir(parents=True)
        (self.root/'repo/scripts/doctor.sh').write_text('fixture')
        self.worker=Worker({'repository':str(self.root/'repo'), 'state':str(self.root/'state'),
                            'home':str(self.root/'home'), 'url':'https://aster.elliottrook.com',
                            'worker_key':'test', 'targets':['doctor']})

    def test_config_publishes_only_complete_verified_bundle(self):
        from types import SimpleNamespace
        self.worker.enabled.add('arista')
        published = self.worker.home/'lab/private-backups'
        published.mkdir(parents=True)
        def export(command, log, timeout, env):
            directory = Path(env['HOMELAB_BACKUP_ROOT'])/'arista/dated'
            directory.mkdir(parents=True)
            for name in REQUIRED['arista']:
                (directory/name).write_text('synthetic configuration')
            self.assertFalse((published/'arista').exists())
            return 0
        with patch.object(self.worker, 'truenas_capacity', return_value=True), patch('worker.subprocess.run', return_value=SimpleNamespace(stdout='')), patch('worker.os.statvfs', return_value=SimpleNamespace(f_bavail=100*1024**3, f_frsize=1)), patch('worker.run', side_effect=export):
            response=self.worker.execute({'id':'a'*32,'target':'arista'})
        self.assertEqual(response['state'],'succeeded')
        self.assertTrue((published/('arista/aster-'+'a'*32)/'dated/running-config.txt').is_file())
        def corrupt(command, log, timeout, env):
            directory=Path(env['HOMELAB_BACKUP_ROOT'])/'arista/dated'
            directory.mkdir(parents=True)
            (directory/'running-config.txt').write_text('incomplete')
            return 0
        with patch.object(self.worker, 'truenas_capacity', return_value=True), patch('worker.subprocess.run', return_value=SimpleNamespace(stdout='')), patch('worker.os.statvfs', return_value=SimpleNamespace(f_bavail=100*1024**3, f_frsize=1)), patch('worker.run', side_effect=corrupt):
            response=self.worker.execute({'id':'b'*32,'target':'arista'})
        self.assertEqual(response['state'],'failed')
        self.assertFalse((published/('arista/aster-'+'b'*32)).exists())

    def test_malformed_claim_cannot_create_pending_file(self):
        with patch.object(self.worker,'call',return_value={'job':{'id':'../../escape','target':'doctor','lease':'b'*64}}):
            with self.assertRaises(ValueError): self.worker.tick()
        self.assertFalse(self.worker.pending.exists())

    def test_guest_result_is_delivered_and_capacity_reservation_is_reduced(self):
        from types import SimpleNamespace
        self.worker.enabled.add('guest-104')
        self.worker.config['guest_key']='synthetic-key-path'
        jid='a'*32
        artifact='vzdump-lxc-104-2026_09_23-13_00_35.tar.zst'
        write_json(self.worker.state/'capacity-reservations.json',{jid:{'reserved':256*1024**3}})
        body={'state':'succeeded','code':'verified','coverage':'local_archive','bytes_verified':12345,'artifact':artifact}
        with patch.object(self.worker,'truenas_capacity',return_value=True), patch('worker.subprocess.run',return_value=SimpleNamespace(stdout=json.dumps(body).encode(),returncode=0)):
            result=self.worker.execute({'id':jid,'target':'guest-104'})
        self.assertEqual(result['state'],'succeeded')
        self.assertNotIn('artifact',result)
        ledger=json.loads((self.worker.state/'capacity-reservations.json').read_text())
        self.assertEqual(ledger[jid]['artifact'],artifact)
        self.assertEqual(ledger[jid]['reserved'],1024**3)

    def test_restart_after_claim_never_executes(self):
        write_json(self.worker.pending, {'id':'a'*32, 'target':'doctor','lease':'b'*64})
        with patch.object(self.worker, 'call', return_value={}) as call, patch.object(self.worker,'execute') as execute:
            self.worker.tick()
            execute.assert_not_called()
            self.assertEqual(call.call_args.args[1]['result']['state'], 'unknown')

    def test_network_failure_retries_result_only(self):
        job={'id':'a'*32, 'target':'doctor','lease':'b'*64}
        verified={'state':'succeeded','code':'checks_complete','coverage':'diagnostic'}
        with patch.object(self.worker, 'call', side_effect=[{'job':job}, OSError('offline')]), patch.object(self.worker, 'execute',return_value=verified) as execute:
            with self.assertRaises(OSError): self.worker.tick()
            execute.assert_called_once()
        with patch.object(self.worker, 'call',return_value={}), patch.object(self.worker, 'execute') as execute:
            self.worker.tick()
            execute.assert_not_called()
        self.assertFalse(self.worker.pending.exists())

    def test_doctor_counts_do_not_forward_raw_log(self):
        def fake(command, log, timeout, env):
            log.write_text('private detail\nPassed: 20\nWarnings: 2\nFailed: 1\n')
            return 1
        with patch('worker.run',side_effect=fake):
            result=self.worker.execute({'target':'doctor'})
        self.assertEqual(result['failures'],1)
        self.assertEqual(result['state'],'succeeded')
        self.assertNotIn('private',json.dumps(result))


if __name__ == '__main__': unittest.main()

class CapacityTests(unittest.TestCase):
    setUp = WorkerTests.setUp
    def test_low_space_and_unavailable_truenas_deny(self):
        from types import SimpleNamespace
        with patch('worker.subprocess.run', return_value=SimpleNamespace(stdout=b'100\n')):
            self.assertFalse(self.worker.truenas_capacity({'id':'a'*32,'target':'guest-104'}))
        with patch('worker.subprocess.run', side_effect=OSError()):
            self.assertFalse(self.worker.truenas_capacity({'id':'a'*32,'target':'nut'}))

    def test_pending_archives_reserve_space_until_mirrored(self):
        from types import SimpleNamespace
        free=815*1024**3
        with patch('worker.subprocess.run', return_value=SimpleNamespace(stdout=str(free).encode())):
            self.assertTrue(self.worker.truenas_capacity({'id':'a'*32,'target':'guest-104'}))
            self.assertTrue(self.worker.truenas_capacity({'id':'b'*32,'target':'guest-109'}))
            self.assertFalse(self.worker.truenas_capacity({'id':'c'*32,'target':'guest-111'}))
        ledger_path=self.worker.state/'capacity-reservations.json'
        ledger=json.loads(ledger_path.read_text())
        ledger['a'*32].update(artifact='vzdump-lxc-104-2026_09_23-12_00_00.tar.zst', bytes_verified=123)
        write_json(ledger_path, ledger)
        def remote(command, **kwargs):
            return SimpleNamespace(stdout=str(123 if 'stat -c' in command[-1] else free).encode())
        with patch('worker.subprocess.run', side_effect=remote):
            self.assertTrue(self.worker.truenas_capacity({'id':'c'*32,'target':'guest-111'}))


class DispatcherTests(unittest.TestCase):
    def test_all_reports_failure_even_if_later_exporters_succeed(self):
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)
            repo=home/'lab/homelab'
            scripts=repo/'scripts/backup'
            scripts.mkdir(parents=True)
            (repo/'scripts/lib').mkdir()
            (repo/'scripts/lib/output.sh').write_text('error(){ echo "$*"; }; warning(){ echo "$*"; }\n')
            for target in ('opnsense','arista','proxmox','nut','observability','video-archiver','guided'):
                p=scripts/(target+'.sh')
                p.write_text('#!/bin/sh\nexit '+('1' if target=='opnsense' else '0')+'\n')
                p.chmod(0o700)
            source=Path(__file__).resolve().parents[2]/'scripts/lab'
            run=subprocess.run(['/bin/bash',str(source),'backup','all'],env={**os.environ,'HOME':str(home)},capture_output=True,text=True)
            self.assertEqual(run.returncode,1)
            self.assertIn('coverage is incomplete',run.stdout)
            self.assertNotIn('exports completed',run.stdout)

class DriftCompatibilityTests(unittest.TestCase):
    def test_drift_selects_newest_artifacts_across_both_layouts(self):
        import subprocess
        source=(Path(__file__).resolve().parents[2]/'scripts/drift-check.sh').read_text()
        functions=source[source.index('latest_file() {'):source.index('require_file() {')]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            old=root/'2026-01-01';old.mkdir()
            new=root/'aster-job/2026-09-23';new.mkdir(parents=True)
            for parent in (old,new): (parent/'running-config.txt').write_text('fixture')
            os.utime(old/'running-config.txt',(1,1))
            output=subprocess.check_output(['/bin/bash','-c',functions+'latest_file "$1" running-config.txt','fixture',str(root)],text=True).strip()
            self.assertEqual(output,str(new/'running-config.txt'))

class RecoveryBundleTests(unittest.TestCase):
    def test_custody_snapshot_can_be_read_in_isolation(self):
        from worker import snapshot_custody
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            custody=root/'custody'; custody.mkdir()
            (custody/'worker.py').write_text('# fixture')
            (custody/'worker.json').write_text('{"synthetic":true}')
            (custody/'toolkit').mkdir()
            self.assertGreater(snapshot_custody(custody,root/'home'),0)
            archive=next((root/'home/lab/private-backups/aster-lab-operations').glob('*.tar.gz'))
            self.assertEqual(archive.stat().st_mode & 0o777,0o600)
            with tarfile.open(archive) as tar:
                self.assertEqual(json.load(tar.extractfile('worker.json')),{'synthetic':True})

    def test_monitor_detects_stale_unknown_and_failed_jobs(self):
        import importlib.util
        path=Path(__file__).resolve().parents[2]/'scripts/check-aster-lab-operations.py'
        spec=importlib.util.spec_from_file_location('lab_probe',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        base={'unknown':0,'running':0,'active_age':0,'queue_age':0,'age':1,'latest_failed':False}
        self.assertEqual(module.classify(base)[0],0)
        for change in ({'unknown':1},{'age':200},{'queue_age':400},{'latest_failed':True}):
            self.assertEqual(module.classify({**base,**change})[0],1)
        self.assertEqual(module.classify({**base,'running':1,'age':200})[0],0)

class GuestPermissionTests(unittest.TestCase):
    def test_native_backup_can_traverse_temp_directory_while_audit_stays_private(self):
        import guest_helper
        import subprocess
        import sys
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); state=root/'state';state.mkdir(); dumps=root/'dump';dumps.mkdir()
            (dumps/'vzdump-lxc-104-old.tar.zst').write_bytes(b'fixture')
            read_text=Path.read_text
            def read(path,*args,**kwargs):
                if str(path)=='/etc/pve/lxc/104.conf': return 'rootfs: local-lvm:test,size=20G\n'
                if str(path)=='/etc/vzdump.conf': return ''
                return read_text(path,*args,**kwargs)
            run=subprocess.run
            def native(command,**kwargs):
                if command[0]=='/usr/sbin/pct': return SimpleNamespace(returncode=0,stdout='status: running\n')
                if command[0]=='/usr/bin/vzdump':
                    self.assertEqual(command[command.index('--remove')+1],'0')
                    run([sys.executable,'-c','import os;os.mkdir('+repr(str(root/'mapped-temp'))+')'],check=True,umask=kwargs['umask'])
                    return SimpleNamespace(returncode=1)  # no synthetic archive claimed
                raise AssertionError(command)
            previous=os.umask(0o077)
            try:
                with patch.object(guest_helper,'STATE',state), patch.object(guest_helper,'BACKUPS',dumps), patch('guest_helper.os.path.ismount',return_value=True), patch('guest_helper.os.statvfs',return_value=SimpleNamespace(f_bavail=2048*1024**3,f_frsize=1)), patch('guest_helper.time.localtime',return_value=SimpleNamespace(tm_hour=12)), patch.object(Path,'read_text',read), patch('guest_helper.subprocess.run',side_effect=native):
                    guest_helper.execute({'id':'a'*32,'target':'guest-104'})
            finally: os.umask(previous)
            self.assertEqual((root/'mapped-temp').stat().st_mode & 0o777,0o755)
            self.assertEqual((state/('a'*32+'.json')).stat().st_mode & 0o777,0o600)
            self.assertEqual((state/'last-operation.log').stat().st_mode & 0o777,0o600)
