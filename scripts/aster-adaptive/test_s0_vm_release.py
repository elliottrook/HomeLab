"""Tests for the stopped Proxmox configuration gate."""

import unittest

import s0_vm_release as release


GOOD = '''balloon: 0
bios: ovmf
boot: order=scsi0
cores: 1
cpu: x86-64-v2-AES
description: Disposable S0 bootstrap canary v1; no vNIC; no corpus
efidisk0: local-lvm:vm-119-disk-1,efitype=4m,pre-enrolled-keys=0,size=4M
hotplug: 0
ide2: local:iso/aster-s0-bootstrap-canary-002.iso,media=cdrom,size=368K
machine: q35
memory: 1024
meta: creation-qemu=11.0.3,ctime=1
name: aster-s0-fixture-v1
onboot: 0
ostype: l26
scsi0: local-lvm:vm-119-disk-0,backup=0,discard=on,size=8G,ssd=1
scsihw: virtio-scsi-single
serial0: socket
smbios1: uuid=00000000-0000-0000-0000-000000000000
sockets: 1
tablet: 0
vga: serial0
vmgenid: 00000000-0000-0000-0000-000000000000
'''


class ReleaseConfigTests(unittest.TestCase):
    def test_exact_config_passes(self):
        self.assertEqual(release.validate_stopped_config(GOOD)['name'], release.NAME)

    def test_network_agent_or_share_fails(self):
        for line in ('net0: virtio=00:00:00:00:00:00,bridge=vmbr0',
                     'agent: 1', 'virtiofs0: shared'):
            with self.assertRaises(release.ConfigError):
                release.validate_stopped_config(GOOD + line + '\n')

    def test_disk_identity_and_limits_fail_closed(self):
        for old, new in (('vm-119-disk-0', 'vm-118-disk-0'), ('size=8G', 'size=9G'),
                         ('memory: 1024', 'memory: 2048'), ('onboot: 0', 'onboot: 1')):
            with self.assertRaises(release.ConfigError):
                release.validate_stopped_config(GOOD.replace(old, new, 1))
        with self.assertRaises(release.ConfigError):
            release.validate_stopped_config(GOOD.replace('vm-119-disk-1', 'vm-119-disk-0'))

    def test_duplicate_or_malformed_line_fails(self):
        for addition in ('memory: 1024\n', 'malformed\n'):
            with self.assertRaises(release.ConfigError):
                release.validate_stopped_config(GOOD + addition)


if __name__ == '__main__':
    unittest.main()
