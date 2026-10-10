"""Idempotent NetBox registration; run through NetBox manage.py shell."""

import os
from django.db import transaction
from dcim.models import MACAddress, Site
from ipam.models import IPAddress, VLAN
from virtualization.models import Cluster, VirtualMachine, VMInterface

APPLY = os.environ.get("TCF_NETBOX_APPLY") == "1"
GUESTS = (
    ("tcf-publisher", "192.168.20.35/24", "BC:24:11:B3:91:18", "Private Content Desk and publisher"),
    ("tcf-origin", "192.168.20.36/24", "BC:24:11:7B:61:6B", "Static public origin; no private mounts"),
)

cluster = Cluster.objects.get(name="proxmox")
site = Site.objects.get(name="Mini Atlas HomeLab")
vlan = VLAN.objects.get(vid=20)
for name, address, mac, description in GUESTS:
    print({"name": name, "address": address, "mac": mac, "apply": APPLY})
    if not APPLY:
        continue
    with transaction.atomic():
        vm, _ = VirtualMachine.objects.update_or_create(
            name=name, defaults={"cluster": cluster, "site": site,
                                 "status": "active", "description": description})
        interface, _ = VMInterface.objects.update_or_create(
            virtual_machine=vm, name="eth0",
            defaults={"mode": "access"})
        interface.untagged_vlan = vlan
        interface.save()
        mac_record, _ = MACAddress.objects.update_or_create(
            mac_address=mac, defaults={"description": description})
        mac_record.assigned_object = interface
        mac_record.save()
        interface.primary_mac_address = mac_record
        interface.save()
        ip, _ = IPAddress.objects.update_or_create(
            address=address, defaults={"status": "active", "description": description})
        ip.assigned_object = interface
        ip.save()
        vm.primary_ip4 = ip
        vm.save()
