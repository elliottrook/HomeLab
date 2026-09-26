"""Local deterministic tests for the bootstrap-canary seed sources."""

import json
import tempfile
import unittest
from pathlib import Path

import s0_vm_candidate as candidate
import s0_vm_serial as serial


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.files = candidate.render()

    def test_deterministic_and_manifest_bound(self):
        self.assertEqual(self.files, candidate.render())
        manifest = json.loads(self.files['candidate-manifest.json'])
        for name, record in manifest['files'].items():
            self.assertEqual(record['bytes'], len(self.files[name]))
            self.assertEqual(record['sha256'], candidate.sha256(self.files[name]))
        self.assertFalse(manifest['iso_created'])
        self.assertFalse(manifest['vm_created'])

    def test_candidate_contains_no_corpus_or_authority(self):
        joined = b'\n'.join(self.files.values())
        for marker in candidate.FORBIDDEN:
            self.assertNotIn(marker.encode(), joined)
        self.assertNotIn(b'evaluation_authorized":true', joined)
        self.assertIn(b'accepted_corpus_included":false', joined)
        self.assertIn(b'infrastructure_authorized":false', joined)

    def test_config_has_no_network_agent_share_or_start(self):
        config = json.loads(self.files['vm-config-proposal.json'])
        self.assertEqual(config['options']['network_devices'], [])
        self.assertEqual(config['options']['agent'], 'absent')
        self.assertFalse(config['start'])
        self.assertEqual(config['options']['onboot'], 0)
        self.assertIn('virtiofs', config['forbidden'])

    def test_cloud_config_has_no_package_or_login_enablement(self):
        user = self.files['user-data']
        for required in (b'package_update: false', b'package_upgrade: false',
                         b'ssh_pwauth: false', b'disable_root: true', b'lock_passwd: true'):
            self.assertIn(required, user)
        for forbidden in (b'password:', b'ssh_authorized_keys', b'apt-get', b'curl ', b'wget '):
            self.assertNotIn(forbidden, user)

    def test_unit_has_outer_limits_and_serial_only_output(self):
        unit = self.files['aster-s0-canary.service']
        for required in (b'NoNewPrivileges=yes', b'CapabilityBoundingSet=', b'PrivateDevices=yes',
                         b'ProtectSystem=strict', b'RestrictAddressFamilies=AF_UNIX',
                         b'MemoryMax=512M', b'RuntimeMaxSec=90', b'TTYPath=/dev/ttyS0'):
            self.assertIn(required, unit)

    def test_canary_result_is_protocol_compatible(self):
        payload = json.loads(self.files['payload-manifest.json'])
        digest = candidate.sha256(candidate.canonical(payload))
        self.assertIn(('MANIFEST = ' + repr(digest)).encode(), self.files['canary.py'])
        value = {'authorization': 'not-granted', 'corpus_evaluated': False, 'fixture': True,
                 'interfaces': ['lo'], 'result': 'bootstrap-canary'}
        decoded = serial.decode_capture(serial.encode_result(value, candidate.RUN_ID, digest),
                                        candidate.RUN_ID, digest)
        self.assertEqual(candidate.validate_canary(decoded['result']), value)

    def test_canary_rejects_interface_or_authority_drift(self):
        base = {'authorization': 'not-granted', 'corpus_evaluated': False, 'fixture': True,
                'interfaces': ['lo'], 'result': 'bootstrap-canary'}
        for key, value in (('interfaces', ['eth0', 'lo']), ('authorization', 'granted'),
                           ('corpus_evaluated', True), ('fixture', False), ('result', 'ok')):
            changed = dict(base); changed[key] = value
            with self.assertRaises(ValueError):
                candidate.validate_canary(changed)
        changed = dict(base); changed['extra'] = True
        with self.assertRaises(ValueError):
            candidate.validate_canary(changed)

    def test_write_is_create_only_and_private(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / 'candidate'
            candidate.write_candidate(target)
            self.assertTrue((target / 'candidate-manifest.json').is_file())
            self.assertEqual((target / 'user-data').stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                candidate.write_candidate(target)


if __name__ == '__main__':
    unittest.main()
