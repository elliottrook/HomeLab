"""Idempotently register the deployed Aster Wiki LXC in NetBox.

Run inside the NetBox Django shell. NetBox remains authoritative after the
initial values have been reconciled from live Proxmox state.
"""

from django.db import transaction
from ipam.models import IPAddress
from virtualization.models import VirtualMachine, VMInterface


with transaction.atomic():
    template = VirtualMachine.objects.get(name="backup-relay")
    vm, created = VirtualMachine.objects.get_or_create(
        name="aster-wiki",
        defaults={
            "cluster": template.cluster,
            "status": "active",
            "vcpus": 2,
            "memory": 2048,
            "disk": 16,
            "description": "Private Aster human knowledge wiki and collector (Proxmox LXC 113)",
        },
    )
    expected = {
        "cluster_id": template.cluster_id,
        "status": "active",
        "vcpus": 2,
        "memory": 2048,
        "disk": 16,
    }
    for field, value in expected.items():
        if getattr(vm, field) != value:
            raise RuntimeError(f"existing aster-wiki {field} differs from live Proxmox state")

    interface, _ = VMInterface.objects.get_or_create(
        virtual_machine=vm, name="eth0", defaults={"enabled": True}
    )
    address, _ = IPAddress.objects.get_or_create(
        address="192.168.20.34/24", defaults={"status": "active"}
    )
    if address.assigned_object not in (None, interface):
        raise RuntimeError("192.168.20.34/24 is already assigned to another NetBox object")
    if address.assigned_object is None:
        address.assigned_object = interface
        address.save()
    if vm.primary_ip4_id != address.id:
        vm.primary_ip4 = address
        vm.save()

print({
    "created": created,
    "vm": vm.name,
    "cluster": vm.cluster.name,
    "interface": interface.name,
    "address": str(address.address),
    "primary_ip4": str(vm.primary_ip4.address),
})
