"""Reconcile the canonical Aster speech service in NetBox.

Run this file through the NetBox Django shell.  It is read-only unless
``ASTER_SPEECH_NETBOX_APPLY=1`` is present in the shell environment.
"""

import os

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from dcim.models import MACAddress
from ipam.models import IPAddress, Service, VLAN
from virtualization.models import VirtualMachine, VMInterface


APPLY = os.environ.get("ASTER_SPEECH_NETBOX_APPLY") == "1"
VM_NAME = "aster-speech"
ADDRESS = "192.168.70.14/24"
MAC = "BC:24:11:E1:11:68"

SERVICES = (
    (
        "Aster speech legacy compatibility API",
        9130,
        "Legacy Piper/STT compatibility endpoint; retained during canonical cutover.",
    ),
    (
        "Aster canonical speech API",
        9131,
        "Canonical Aster voice (Kokoro bm_daniel, en-gb, speed 0.95); interactive and batch synthesis plus health and metrics.",
    ),
    (
        "Aster Wyoming TTS",
        10300,
        "Home Assistant Wyoming TTS endpoint; network policy restricts the consumer to home-assistant (192.168.20.11).",
    ),
)


vm = VirtualMachine.objects.get(name=VM_NAME)
interface = VMInterface.objects.get(virtual_machine=vm, name="eth0")
address = IPAddress.objects.get(address=ADDRESS)
vlan = VLAN.objects.get(vid=70)

expected = {
    "status": "active",
    "vcpus": 6,
    "memory": 4096,
    "disk": 16,
}
for field, value in expected.items():
    if getattr(vm, field) != value:
        raise RuntimeError(
            f"NetBox {VM_NAME} {field}={getattr(vm, field)!r}; live Proxmox requires {value!r}"
        )
if address.assigned_object != interface:
    raise RuntimeError(f"{ADDRESS} is not assigned to {VM_NAME}/eth0")
if vm.primary_ip4 != address:
    raise RuntimeError(f"{ADDRESS} is not the primary IPv4 address for {VM_NAME}")

print(
    {
        "apply": APPLY,
        "vm": VM_NAME,
        "address": ADDRESS,
        "mac": MAC,
        "vlan": vlan.name,
        "services": [f"tcp/{port}" for _, port, _ in SERVICES],
    }
)

if APPLY:
    with transaction.atomic():
        vm.description = (
            "Canonical Aster network speech service, Proxmox LXC 116, "
            "private Lab VLAN 70"
        )
        vm.save()

        interface.enabled = True
        interface.mode = "access"
        interface.untagged_vlan = vlan
        interface.save()

        mac_record, _ = MACAddress.objects.update_or_create(
            mac_address=MAC,
            defaults={"description": "aster-speech eth0 (Proxmox LXC 116)"},
        )
        if mac_record.assigned_object not in (None, interface):
            raise RuntimeError(f"{MAC} is assigned to another NetBox object")
        mac_record.assigned_object = interface
        mac_record.save()
        interface.primary_mac_address = mac_record
        interface.save()

        content_type = ContentType.objects.get_for_model(vm)
        for name, port, description in SERVICES:
            Service.objects.update_or_create(
                parent_object_type=content_type,
                parent_object_id=vm.pk,
                name=name,
                defaults={
                    "protocol": "tcp",
                    "ports": [port],
                    "description": description,
                },
            )

print(
    {
        "description": vm.description,
        "services": list(
            Service.objects.filter(
                parent_object_type=ContentType.objects.get_for_model(vm),
                parent_object_id=vm.pk,
            ).values_list("name", "protocol", "ports")
        ),
    }
)
