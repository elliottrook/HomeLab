"""Tests for the exact corrected V3b stopped-VM configuration gate."""

import re
import unittest
from pathlib import Path

import s0_vm_isolation_candidate_v2 as candidate
import s0_vm_isolation_release_v2 as release


GOOD = '''balloon: 0
bios: ovmf
boot: order=scsi0
cores: 1
cpu: x86-64-v2-AES
description: Disposable S0 corrected isolation fixture; no vNIC; no corpus
efidisk0: local-lvm:vm-121-disk-1,efitype=4m,pre-enrolled-keys=0,size=4M
hotplug: 0
ide2: local:iso/aster-s0-isolation-fixture-002.iso,media=cdrom,size=372K
machine: q35
memory: 1024
meta: creation-qemu=11.0.3,ctime=1790470000
name: aster-s0-isolation-v2
onboot: 0
ostype: l26
scsi0: local-lvm:vm-121-disk-0,backup=0,discard=on,size=8G,ssd=1
scsihw: virtio-scsi-single
serial0: socket
smbios1: uuid=00000000-0000-0000-0000-000000000000
sockets: 1
tablet: 0
vga: serial0
vmgenid: 00000000-0000-0000-0000-000000000000
'''


class CorrectedIsolationReleaseTests(unittest.TestCase):
    def test_accepts_exact_offline_shape(self):
        self.assertEqual(release.validate_stopped_config(GOOD)['name'], release.NAME)

    def test_rejects_network_agent_passthrough_and_identity_drift(self):
        changes = [GOOD + line for line in (
            'net0: virtio=00:11:22:33:44:55,bridge=vmbr0\n', 'agent: 1\n',
            'hostpci0: 01:00.0\n', 'virtiofs0: share\n')]
        changes += [GOOD.replace(old, new) for old, new in (
            ('aster-s0-isolation-v2', 'wrong'), ('memory: 1024', 'memory: 2048'),
            ('vm-121-disk-0', 'vm-120-disk-0'),
            ('aster-s0-isolation-fixture-002.iso', 'other.iso'))]
        for changed in changes:
            with self.assertRaises(release.ConfigError):
                release.validate_stopped_config(changed)

    def test_release_script_pins_candidate_and_validator(self):
        root = Path(__file__).resolve().parents[2]
        script = (root / 'docs/projects/AI Projects/experiments/s0-routing-descriptive-v1/'
                  'vm-release-v3b/create-stopped-vm-v3b.sh').read_text()
        rendered = candidate.render()
        expected = {
            'USER': candidate.sha256(rendered['user-data']),
            'META': candidate.sha256(rendered['meta-data']),
            'CANDIDATE': candidate.sha256(rendered['candidate-manifest.json']),
            'VALIDATOR': candidate.sha256((root / 'scripts/aster-adaptive/'
                                           's0_vm_isolation_release_v2.py').read_bytes()),
        }
        for label, digest in expected.items():
            match = re.search(r'^EXPECTED_' + label + r'_SHA256=([0-9a-f]{64})$',
                              script, re.MULTILINE)
            self.assertIsNotNone(match)
            self.assertEqual(match.group(1), digest)


if __name__ == '__main__':
    unittest.main()
