#!/usr/bin/env python3
"""Register the bounded Aster Games LXC identity in NetBox."""

from __future__ import annotations

import json
import os


NAME = "aster-games"
ADDRESS = "192.168.20.38/24"
DNS_NAME = "aster-games.home.internal"
MAC = "BC:24:11:54:B1:E5"
VMID = "129"
VLAN_ID = 20
SERVICES = {
    "RomM administration": ("tcp", (8080,)),
    "ROMarr administration": ("tcp", (6868,)),
}


def execute(mode: str) -> dict:
    if mode not in {"check", "apply", "rollback"}:
        raise ValueError("mode")

    from django.db import transaction
    from dcim.models import MACAddress, Site
    from ipam.models import IPAddress, Prefix, Service, VLAN
    from virtualization.models import Cluster, VirtualMachine, VMInterface

    cluster = Cluster.objects.get(name="proxmox")
    site = Site.objects.get(slug="mini-atlas")
    vlan = VLAN.objects.get(vid=VLAN_ID)
    prefix = Prefix.objects.get(prefix="192.168.20.0/24")
    if prefix.vlan_id != vlan.id:
        raise RuntimeError("servers-prefix-vlan-mismatch")

    existing = VirtualMachine.objects.filter(name=NAME).first()
    if mode == "rollback":
        if existing is None:
            return {"outcome": "already-absent", "virtual_machine": NAME}
        interface = existing.interfaces.filter(name="eth0").first()
        if (
            existing.serial != VMID
            or interface is None
            or str(interface.primary_mac_address) != MAC
            or str(existing.primary_ip4) != ADDRESS
        ):
            raise RuntimeError("rollback-identity-mismatch")
        with transaction.atomic():
            Service.objects.filter(virtual_machine=existing, name__in=SERVICES).delete()
            IPAddress.objects.filter(address=ADDRESS, assigned_object_id=interface.id).delete()
            MACAddress.objects.filter(mac_address=MAC, assigned_object_id=interface.id).delete()
            existing.delete()
        return {"outcome": "rolled-back", "virtual_machine": NAME}

    conflicts = {
        "name": list(VirtualMachine.objects.filter(name=NAME).values_list("id", flat=True)),
        "vmid": list(VirtualMachine.objects.filter(serial=VMID).values_list("id", flat=True)),
        "mac": list(MACAddress.objects.filter(mac_address=MAC).values_list("id", flat=True)),
        "address": [
            str(value)
            for value in IPAddress.objects.filter(
                address__net_host=ADDRESS.split("/", 1)[0]
            ).values_list("address", flat=True)
        ],
    }
    if any(conflicts.values()):
        if existing is not None:
            interface = existing.interfaces.filter(name="eth0").first()
            service_state = {
                item.name: (item.protocol, tuple(item.ports))
                for item in Service.objects.filter(virtual_machine=existing, name__in=SERVICES)
            }
            exact = (
                existing.serial == VMID
                and existing.cluster_id == cluster.id
                and existing.site_id == site.id
                and existing.vcpus == 4
                and existing.memory == 6144
                and existing.disk == 96
                and interface is not None
                and interface.untagged_vlan_id == vlan.id
                and str(interface.primary_mac_address) == MAC
                and str(existing.primary_ip4) == ADDRESS
                and service_state == SERVICES
            )
            if exact:
                return {
                    "outcome": "already-present",
                    "virtual_machine_id": existing.id,
                    "services": sorted(service_state),
                }
        raise RuntimeError("netbox-identity-conflict:" + json.dumps(conflicts, sort_keys=True))

    if mode == "check":
        return {
            "outcome": "ready",
            "virtual_machine": NAME,
            "cluster": cluster.name,
            "site": site.name,
            "vlan": vlan.name,
        }

    with transaction.atomic():
        virtual_machine = VirtualMachine.objects.create(
            name=NAME,
            serial=VMID,
            cluster=cluster,
            site=site,
            status="active",
            vcpus=4,
            memory=6144,
            disk=96,
            description="Aster Games server infrastructure; owner: HomeLab operations",
            comments=(
                "Stream A infrastructure for RomM, ROMarr, and the Aster Games broker. "
                "AsterTV device integration remains gated pending v3 deployment and acceptance."
            ),
        )
        interface = VMInterface.objects.create(
            virtual_machine=virtual_machine,
            name="eth0",
            enabled=True,
            mode="access",
            untagged_vlan=vlan,
            description="Proxmox LXC 129 VLAN 20",
        )
        mac = MACAddress.objects.create(mac_address=MAC, assigned_object=interface)
        interface.primary_mac_address = mac
        interface.save(update_fields=["primary_mac_address"])
        address = IPAddress.objects.create(
            address=ADDRESS,
            status="active",
            dns_name=DNS_NAME,
            assigned_object=interface,
        )
        virtual_machine.primary_ip4 = address
        virtual_machine.save(update_fields=["primary_ip4"])
        for service_name, (protocol, ports) in SERVICES.items():
            Service.objects.create(
                parent=virtual_machine,
                name=service_name,
                protocol=protocol,
                ports=ports,
                description="Private administration endpoint; no public ingress",
            )

    return {
        "outcome": "created",
        "virtual_machine_id": virtual_machine.id,
        "interface_id": interface.id,
        "mac_id": mac.id,
        "address_id": address.id,
        "services": sorted(SERVICES),
    }


if __name__ in {"__main__", "django.core.management.commands.shell"}:
    print(json.dumps(execute(os.environ.get("ASTER_GAMES_NETBOX_MODE", "check")), sort_keys=True))
