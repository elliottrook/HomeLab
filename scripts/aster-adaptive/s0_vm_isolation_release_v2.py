"""Validate the exact stopped Proxmox configuration for the V3b corrected fixture."""

import re


VMID = 121
ISO_NAME = 'aster-s0-isolation-fixture-002.iso'
NAME = 'aster-s0-isolation-v2'


class ConfigError(ValueError):
    pass


def parse_config(text):
    result = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        if ': ' not in line:
            raise ConfigError('malformed config line')
        key, value = line.split(': ', 1)
        if key in result:
            raise ConfigError('duplicate config key')
        result[key] = value
    return result


def _disk(value):
    parts = value.split(',')
    options = {}
    for item in parts[1:]:
        if '=' not in item:
            raise ConfigError('malformed disk option')
        key, option = item.split('=', 1)
        if key in options:
            raise ConfigError('duplicate disk option')
        options[key] = option
    return parts[0], options


def validate_stopped_config(text, vmid=VMID):
    config = parse_config(text)
    allowed = {
        'balloon', 'bios', 'boot', 'cores', 'cpu', 'description', 'efidisk0',
        'hotplug', 'ide2', 'machine', 'memory', 'meta', 'name', 'onboot',
        'ostype', 'scsi0', 'scsihw', 'serial0', 'smbios1', 'sockets', 'tablet',
        'vga', 'vmgenid',
    }
    unexpected = set(config) - allowed
    if unexpected:
        raise ConfigError('unexpected config keys: ' + ','.join(sorted(unexpected)))
    exact = {
        'balloon': '0', 'bios': 'ovmf', 'boot': 'order=scsi0', 'cores': '1',
        'cpu': 'x86-64-v2-AES',
        'description': 'Disposable S0 corrected isolation fixture; no vNIC; no corpus',
        'hotplug': '0', 'machine': 'q35', 'memory': '1024', 'name': NAME,
        'onboot': '0', 'ostype': 'l26', 'scsihw': 'virtio-scsi-single',
        'serial0': 'socket', 'sockets': '1', 'tablet': '0', 'vga': 'serial0',
    }
    for key, expected in exact.items():
        if config.get(key) != expected:
            raise ConfigError(key + ' mismatch')
    scsi_volume, scsi_options = _disk(config.get('scsi0', ''))
    if not re.fullmatch(r'local-lvm:vm-' + str(vmid) + r'-disk-\d+', scsi_volume):
        raise ConfigError('scsi0 volume mismatch')
    if scsi_options != {'backup': '0', 'discard': 'on', 'size': '8G', 'ssd': '1'}:
        raise ConfigError('scsi0 options mismatch')
    efi_volume, efi_options = _disk(config.get('efidisk0', ''))
    if not re.fullmatch(r'local-lvm:vm-' + str(vmid) + r'-disk-\d+', efi_volume):
        raise ConfigError('efidisk0 volume mismatch')
    if efi_volume == scsi_volume:
        raise ConfigError('disk volumes must be distinct')
    if efi_options != {'efitype': '4m', 'pre-enrolled-keys': '0', 'size': '4M'}:
        raise ConfigError('efidisk0 options mismatch')
    iso_volume, iso_options = _disk(config.get('ide2', ''))
    if iso_volume != 'local:iso/' + ISO_NAME or iso_options.get('media') != 'cdrom':
        raise ConfigError('seed ISO mismatch')
    if set(iso_options) - {'media', 'size'}:
        raise ConfigError('unexpected seed options')
    return config


def main(path):
    if path == '-':
        import sys
        text = sys.stdin.read()
    else:
        with open(path, encoding='utf-8') as handle:
            text = handle.read()
    validate_stopped_config(text)
    print('stopped_config=pass')


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        raise SystemExit('usage: s0_vm_isolation_release.py QM-CONFIG|-')
    main(sys.argv[1])
