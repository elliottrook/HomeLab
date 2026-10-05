"""Tests for the corrected V3b invented-fixture candidate."""

import json
import tempfile
import unittest
from pathlib import Path

import s0_vm_isolation_candidate_v2 as candidate
import s0_vm_serial as serial


class CorrectedIsolationCandidateTests(unittest.TestCase):
    def setUp(self):
        self.files = candidate.render()

    def test_deterministic_and_manifest_bound(self):
        self.assertEqual(self.files, candidate.render())
        manifest = json.loads(self.files['candidate-manifest.json'])
        self.assertEqual(manifest['run_id'], 'isolation-fixture-002')
        self.assertEqual(manifest['instance_id'], 'aster-s0-isolation-fixture-002')
        for name, record in manifest['files'].items():
            self.assertEqual(record['bytes'], len(self.files[name]))
            self.assertEqual(record['sha256'], candidate.sha256(self.files[name]))

    def test_correction_preserves_private_tmp_and_moves_only_denial_target(self):
        unit = self.files['aster-s0-isolation.service']
        user = self.files['user-data']
        probe = self.files['isolation_probe.py']
        self.assertIn(b'PrivateTmp=yes', unit)
        self.assertIn(b'InaccessiblePaths=/srv/aster-s0-isolation-fixture-002', unit)
        self.assertIn(b'/srv/aster-s0-isolation-fixture-002/canary', probe)
        self.assertIn(b'/srv/aster-s0-isolation-fixture-002/canary', user)
        joined = b'\n'.join(self.files.values())
        self.assertNotIn(b'/var/tmp/aster-s0-isolation-fixture-001', joined)

    def test_security_bounds_and_offline_config_remain(self):
        unit = self.files['aster-s0-isolation.service']
        for required in (b'PrivateNetwork=yes', b'ProtectSystem=strict',
                         b'SystemCallFilter=~@network-io clone clone3 fork vfork',
                         b'ReadWritePaths=/var/lib/aster-s0/output',
                         b'MemoryMax=64M', b'MemorySwapMax=0', b'TasksMax=1',
                         b'LimitFSIZE=8192', b'TimeoutStartSec=15'):
            self.assertIn(required, unit)
        config = json.loads(self.files['vm-config-proposal.json'])
        self.assertEqual(config['options']['network_devices'], [])
        self.assertEqual(config['options']['agent'], 'absent')
        self.assertFalse(config['start'])

    def test_no_corpus_credentials_or_package_fetch(self):
        joined = b'\n'.join(self.files.values())
        for marker in candidate.FORBIDDEN:
            self.assertNotIn(marker.encode(), joined)
        for forbidden in (b'evaluation_authorized":true', b'credentials_authorized":true',
                          b'network_attachment_authorized":true', b'apt-get', b'curl ', b'wget '):
            self.assertNotIn(forbidden, joined)

    def test_result_protocol_and_fail_closed_validation(self):
        payload = json.loads(self.files['payload-manifest.json'])
        digest = candidate.sha256(candidate.canonical(payload))
        checks = {name: True for name in payload['required_checks']}
        value = {'authorization': 'invented-fixture-only', 'checks': checks,
                 'corpus_evaluated': False, 'fixture': True, 'result': 'isolation-pass'}
        decoded = serial.decode_capture(serial.encode_result(value, candidate.RUN_ID, digest),
                                        candidate.RUN_ID, digest)
        self.assertEqual(candidate.validate_result(decoded['result']), value)
        changed = json.loads(json.dumps(value)); changed['checks']['unrelated_read_denied'] = False
        with self.assertRaises(ValueError):
            candidate.validate_result(changed)

    def test_write_is_create_only_and_repository_candidate_matches(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / 'candidate'
            candidate.write_candidate(target)
            with self.assertRaises(FileExistsError):
                candidate.write_candidate(target)
        root = (Path(__file__).resolve().parents[2] /
                'docs/projects/AI Projects/experiments/s0-routing-descriptive-v1/'
                'vm-isolation-candidate-v2')
        for name, raw in self.files.items():
            self.assertEqual((root / name).read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
