"""Reconcile the Aster web and agent API service in NetBox.

Run through the NetBox Django shell. It is read-only unless
``ASTER_AGENT_NETBOX_APPLY=1`` is present in the shell environment.
"""

import os

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from ipam.models import IPAddress, Service
from virtualization.models import VirtualMachine, VMInterface


APPLY = os.environ.get("ASTER_AGENT_NETBOX_APPLY") == "1"
VM_NAME = "hermesagent"
ADDRESS = "192.168.70.10/24"
SERVICE_NAME = "Aster web and agent API"

vm = VirtualMachine.objects.get(name=VM_NAME)
interface = VMInterface.objects.get(virtual_machine=vm, name="eth0")
address = IPAddress.objects.get(address=ADDRESS)

if str(vm.status) != "active":
    raise RuntimeError(f"NetBox {VM_NAME} status={vm.status!s}; expected active")
if address.assigned_object != interface or vm.primary_ip4 != address:
    raise RuntimeError(f"{ADDRESS} is not the primary address on {VM_NAME}/eth0")

content_type = ContentType.objects.get_for_model(vm)
defaults = {
    "protocol": "tcp",
    "ports": [9120],
    "description": (
        "Aster web interface and authenticated agent API. Canonical public UI: "
        "https://aster.elliottrook.com/; /companion is a compatibility alias."
    ),
}

print({"apply": APPLY, "vm": VM_NAME, "address": ADDRESS, "service": SERVICE_NAME})

if APPLY:
    with transaction.atomic():
        Service.objects.update_or_create(
            parent_object_type=content_type,
            parent_object_id=vm.pk,
            name=SERVICE_NAME,
            defaults=defaults,
        )

print(
    list(
        Service.objects.filter(
            parent_object_type=content_type,
            parent_object_id=vm.pk,
            name=SERVICE_NAME,
        ).values("id", "name", "protocol", "ports", "description")
    )
)
