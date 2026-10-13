"""Idempotently register the production Aster voice LXC in NetBox.

Run through the NetBox Django shell after reconciling the MAC address from live
Proxmox state. The script is read-only unless ASTER_VOICE_PROD_NETBOX_APPLY=1.
"""

import os

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from dcim.models import MACAddress, Site
from ipam.models import IPAddress, Service, VLAN
from virtualization.models import Cluster, VirtualMachine, VMInterface


APPLY = os.environ.get("ASTER_VOICE_PROD_NETBOX_APPLY") == "1"
MAC = os.environ.get("ASTER_VOICE_PROD_MAC", "").upper()
VM_NAME = "aster-voice-prod"
ADDRESS = "192.168.20.37/24"
VMID = 128

if not MAC:
    raise RuntimeError("ASTER_VOICE_PROD_MAC must be reconciled from live Proxmox state")

SERVICES = (
    ("Aster production speech compatibility API", 9130),
    ("Aster production canonical speech API", 9131),
    ("Aster production Wyoming speech", 10300),
)

cluster = Cluster.objects.get(name="proxmox")
site = Site.objects.get(name="Mini Atlas HomeLab")
vlan = VLAN.objects.get(vid=20)
existing_ip = IPAddress.objects.filter(address=ADDRESS).first()
existing_vm = VirtualMachine.objects.filter(name=VM_NAME).first()

if existing_ip and (
    existing_vm is None
    or existing_ip.assigned_object is None
    or existing_ip.assigned_object.virtual_machine_id != existing_vm.id
):
    raise RuntimeError(f"{ADDRESS} is already assigned to another NetBox object")

print({"apply": APPLY, "vm": VM_NAME, "vmid": VMID, "address": ADDRESS,
       "mac": MAC, "vlan": vlan.name})

if APPLY:
    with transaction.atomic():
        vm, _ = VirtualMachine.objects.update_or_create(
            name=VM_NAME,
            defaults={
                "cluster": cluster,
                "site": site,
                "status": "active",
                "vcpus": 6,
                "memory": 4096,
                "disk": 16,
                "description": (
                    "Production Aster voice service, Proxmox LXC 128, "
                    "private Servers VLAN 20"
                ),
            },
        )
        interface, _ = VMInterface.objects.update_or_create(
            virtual_machine=vm,
            name="eth0",
            defaults={"enabled": True, "mode": "access", "untagged_vlan": vlan},
        )
        mac_record, _ = MACAddress.objects.update_or_create(
            mac_address=MAC,
            defaults={"description": "aster-voice-prod eth0 (Proxmox LXC 128)"},
        )
        if mac_record.assigned_object not in (None, interface):
            raise RuntimeError(f"{MAC} is assigned to another NetBox object")
        mac_record.assigned_object = interface
        mac_record.save()
        interface.primary_mac_address = mac_record
        interface.save()

        address, _ = IPAddress.objects.update_or_create(
            address=ADDRESS,
            defaults={"status": "active", "description": "Aster voice production"},
        )
        address.assigned_object = interface
        address.save()
        vm.primary_ip4 = address
        vm.save()

        content_type = ContentType.objects.get_for_model(vm)
        for name, port in SERVICES:
            Service.objects.update_or_create(
                parent_object_type=content_type,
                parent_object_id=vm.pk,
                name=name,
                defaults={"protocol": "tcp", "ports": [port]},
            )

vm = VirtualMachine.objects.get(name=VM_NAME) if APPLY else existing_vm
print({
    "registered": vm is not None,
    "services": [] if vm is None else list(
        Service.objects.filter(
            parent_object_type=ContentType.objects.get_for_model(vm),
            parent_object_id=vm.pk,
        ).values_list("name", "protocol", "ports")
    ),
})
