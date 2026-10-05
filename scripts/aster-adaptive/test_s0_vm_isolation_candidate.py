"""Deterministic tests for the V3 invented-fixture isolation candidate."""

import json
import tempfile
import unittest
from pathlib import Path

import s0_vm_isolation_candidate as candidate
import s0_vm_serial as serial


class IsolationCandidateTests(unittest.TestCase):
    def setUp(self):
        self.files = candidate.render()

    def test_deterministic_and_manifest_bound(self):
        self.assertEqual(self.files, candidate.render())
        manifest = json.loads(self.files['candidate-manifest.json'])
        for name, record in manifest['files'].items():
            self.assertEqual(record['bytes'], len(self.files[name]))
            self.assertEqual(record['sha256'], candidate.sha256(self.files[name]))
        self.assertFalse(manifest['executed'])

    def test_candidate_contains_no_corpus_or_authority(self):
        joined = b'\n'.join(self.files.values())
        for marker in candidate.FORBIDDEN:
            self.assertNotIn(marker.encode(), joined)
        for forbidden in (b'evaluation_authorized":true', b'credentials_authorized":true',
                          b'network_attachment_authorized":true'):
            self.assertNotIn(forbidden, joined)
        self.assertIn(b'accepted_corpus_included":false', joined)

    def test_config_is_offline_and_stopped(self):
        config = json.loads(self.files['vm-config-proposal.json'])
        self.assertEqual(config['options']['network_devices'], [])
        self.assertEqual(config['options']['agent'], 'absent')
        self.assertFalse(config['start'])
        self.assertEqual(config['options']['onboot'], 0)

    def test_cloud_config_has_no_packages_credentials_or_login(self):
        user = self.files['user-data']
        for required in (b'package_update: false', b'package_upgrade: false',
                         b'ssh_pwauth: false', b'disable_root: true', b'lock_passwd: true'):
            self.assertIn(required, user)
        for forbidden in (b'password:', b'ssh_authorized_keys', b'apt-get', b'curl ', b'wget '):
            self.assertNotIn(forbidden, user)

    def test_unit_has_required_os_controls_and_bounds(self):
        unit = self.files['aster-s0-isolation.service']
        for required in (b'NoNewPrivileges=yes', b'PrivateNetwork=yes',
                         b'ProtectSystem=strict', b'SystemCallFilter=~@network-io clone clone3 fork vfork',
                         b'InaccessiblePaths=/var/tmp/aster-s0-isolation-fixture-001',
                         b'ReadWritePaths=/var/lib/aster-s0/output', b'MemoryMax=64M',
                         b'MemorySwapMax=0', b'TasksMax=1', b'LimitFSIZE=8192',
                         b'RuntimeMaxSec=15', b'TimeoutStartSec=15'):
            self.assertIn(required, unit)

    def test_probe_contains_every_negative_check(self):
        probe = self.files['isolation_probe.py']
        for required in (b'inet_socket_denied', b'unix_socket_denied', b'fork_denied',
                         b'unrelated_read_denied', b'system_write_denied',
                         b'environment_allowlisted', b'loopback_only'):
            self.assertIn(required, probe)

    def test_result_validator_is_fail_closed(self):
        checks = {name: True for name in json.loads(self.files['payload-manifest.json'])['required_checks']}
        value = {'authorization': 'invented-fixture-only', 'checks': checks,
                 'corpus_evaluated': False, 'fixture': True, 'result': 'isolation-pass'}
        self.assertEqual(candidate.validate_result(value), value)
        for name in checks:
            changed = json.loads(json.dumps(value)); changed['checks'][name] = False
            with self.assertRaises(ValueError):
                candidate.validate_result(changed)
        changed = dict(value); changed['extra'] = True
        with self.assertRaises(ValueError):
            candidate.validate_result(changed)

    def test_result_is_serial_protocol_compatible(self):
        payload = json.loads(self.files['payload-manifest.json'])
        digest = candidate.sha256(candidate.canonical(payload))
        checks = {name: True for name in payload['required_checks']}
        value = {'authorization': 'invented-fixture-only', 'checks': checks,
                 'corpus_evaluated': False, 'fixture': True, 'result': 'isolation-pass'}
        decoded = serial.decode_capture(serial.encode_result(value, candidate.RUN_ID, digest),
                                        candidate.RUN_ID, digest)
        self.assertEqual(candidate.validate_result(decoded['result']), value)

    def test_write_is_create_only(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / 'candidate'
            candidate.write_candidate(target)
            with self.assertRaises(FileExistsError):
                candidate.write_candidate(target)

    def test_repository_candidate_matches_renderer(self):
        root = (Path(__file__).resolve().parents[2] /
                'docs/projects/AI Projects/experiments/s0-routing-descriptive-v1/'
                'vm-isolation-candidate-v1')
        for name, raw in self.files.items():
            self.assertEqual((root / name).read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
