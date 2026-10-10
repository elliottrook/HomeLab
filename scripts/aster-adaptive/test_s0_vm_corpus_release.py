import unittest

import s0_vm_corpus_release as release


def config():
    return '''balloon: 0
bios: ovmf
boot: order=scsi0
cores: 1
cpu: x86-64-v2-AES
description: Disposable S0 accepted-corpus descriptive run; no vNIC; no credentials
efidisk0: local-lvm:vm-122-disk-1,efitype=4m,pre-enrolled-keys=0,size=4M
hotplug: 0
ide2: local:iso/aster-s0-corpus-descriptive-001.iso,media=cdrom,size=500K
machine: q35
memory: 1024
meta: creation-qemu=11.0.3,ctime=1
name: aster-s0-corpus-v1
onboot: 0
ostype: l26
scsi0: local-lvm:vm-122-disk-0,backup=0,discard=on,size=8G,ssd=1
scsihw: virtio-scsi-single
serial0: socket
smbios1: uuid=00000000-0000-0000-0000-000000000000
sockets: 1
tablet: 0
vga: serial0
vmgenid: 00000000-0000-0000-0000-000000000001
'''


class CorpusReleaseTest(unittest.TestCase):
    def test_exact_config(self):
        self.assertEqual(release.validate_stopped_config(config())['name'], release.NAME)

    def test_rejects_network_agent_and_drift(self):
        for changed in (config() + 'net0: virtio=00:11:22:33:44:55\n',
                        config() + 'agent: 1\n',
                        config().replace('memory: 1024', 'memory: 2048'),
                        config().replace('vm-122-disk-0', 'vm-121-disk-0')):
            with self.assertRaises(release.ConfigError):
                release.validate_stopped_config(changed)


if __name__ == '__main__':
    unittest.main()
