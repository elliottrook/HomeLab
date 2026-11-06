#!/usr/bin/env python3
"""Bounded NetBox registration for the independently verified Family client."""
from __future__ import annotations

import json
import os


DEVICE = "AsterTV-Family"
SERIAL = "L0E3N950CDB07220291"
MANUFACTURER = "BOSGAME"
DEVICE_TYPE = "BOSGAME Ecolite Series"
DEVICE_TYPE_SLUG = "bosgame-ecolite-series"
ROLE_SLUG = "media-client"
SITE_SLUG = "mini-atlas"
INTERFACE = "eth0"
INTERFACE_TYPE = "1000base-t"
MAC = "84:47:09:A1:D3:55"
ADDRESS = "192.168.1.157/24"
DNS_NAME = "astertv-family.home.internal"
VLAN_ID = 10


def execute(mode: str) -> dict:
    if mode not in {"check", "apply", "rollback"}:
        raise ValueError("mode")
    from django.db import transaction
    from dcim.models import Device, DeviceRole, DeviceType, Interface, MACAddress, Manufacturer, Site
    from ipam.models import IPAddress, Prefix, VLAN

    role = DeviceRole.objects.get(slug=ROLE_SLUG)
    site = Site.objects.get(slug=SITE_SLUG)
    vlan = VLAN.objects.get(vid=VLAN_ID)
    prefix = Prefix.objects.get(prefix="192.168.1.0/24")
    if prefix.vlan_id != vlan.id:
        raise RuntimeError("trusted-prefix-vlan-mismatch")

    existing = Device.objects.filter(name=DEVICE).first()
    if mode == "rollback":
        if existing is None:
            return {"outcome": "already-absent", "device": DEVICE}
        interface = existing.interfaces.filter(name=INTERFACE).first()
        if (existing.serial != SERIAL or interface is None or
                str(interface.primary_mac_address) != MAC or
                str(existing.primary_ip4) != ADDRESS):
            raise RuntimeError("rollback-identity-mismatch")
        with transaction.atomic():
            IPAddress.objects.filter(address=ADDRESS, assigned_object_id=interface.id).delete()
            MACAddress.objects.filter(mac_address=MAC, assigned_object_id=interface.id).delete()
            device_type = existing.device_type
            manufacturer = device_type.manufacturer
            existing.delete()
            if not Device.objects.filter(device_type=device_type).exists():
                device_type.delete()
            if not DeviceType.objects.filter(manufacturer=manufacturer).exists():
                manufacturer.delete()
        return {"outcome": "rolled-back", "device": DEVICE}

    conflicts = {
        "device": list(Device.objects.filter(name=DEVICE).values_list("id", flat=True)),
        "serial": list(Device.objects.filter(serial=SERIAL).values_list("id", flat=True)),
        "mac": list(MACAddress.objects.filter(mac_address=MAC).values_list("id", flat=True)),
        "address": [str(value) for value in IPAddress.objects.filter(
            address__net_host=ADDRESS.split("/", 1)[0]).values_list("address", flat=True)],
    }
    if any(conflicts.values()):
        if existing and existing.serial == SERIAL and str(existing.primary_ip4) == ADDRESS:
            interface = existing.interfaces.filter(name=INTERFACE).first()
            if (interface is None or str(interface.primary_mac_address) != MAC or
                    existing.device_type.slug != DEVICE_TYPE_SLUG or
                    existing.role.slug != ROLE_SLUG or existing.site.slug != SITE_SLUG):
                raise RuntimeError("existing-device-contract-mismatch")
            return {"outcome": "already-present", "device_id": existing.id,
                    "conflicts": conflicts}
        raise RuntimeError("netbox-identity-conflict:" + json.dumps(conflicts, sort_keys=True))
    if mode == "check":
        return {"outcome": "ready", "device": DEVICE, "site": site.name,
                "role": role.name, "vlan": vlan.name, "prefix": str(prefix.prefix)}

    with transaction.atomic():
        manufacturer, _ = Manufacturer.objects.get_or_create(
            name=MANUFACTURER, defaults={"slug": "bosgame"})
        if manufacturer.slug != "bosgame":
            raise RuntimeError("manufacturer-slug-mismatch")
        device_type, _ = DeviceType.objects.get_or_create(
            slug=DEVICE_TYPE_SLUG,
            defaults={"model": DEVICE_TYPE, "manufacturer": manufacturer})
        if device_type.model != DEVICE_TYPE or device_type.manufacturer_id != manufacturer.id:
            raise RuntimeError("device-type-mismatch")
        device = Device.objects.create(
            name=DEVICE, serial=SERIAL, device_type=device_type, role=role,
            site=site, status="active")
        interface = Interface.objects.create(
            device=device, name=INTERFACE, type=INTERFACE_TYPE, enabled=True)
        mac = MACAddress.objects.create(mac_address=MAC, assigned_object=interface)
        interface.primary_mac_address = mac
        interface.save(update_fields=["primary_mac_address"])
        address = IPAddress.objects.create(
            address=ADDRESS, status="active", dns_name=DNS_NAME,
            assigned_object=interface)
        device.primary_ip4 = address
        device.save(update_fields=["primary_ip4"])
    return {"outcome": "created", "device_id": device.id,
            "interface_id": interface.id, "mac_id": mac.id, "address_id": address.id}


if __name__ in {"__main__", "django.core.management.commands.shell"}:
    print(json.dumps(execute(os.environ.get("ASTERTV_NETBOX_MODE", "check")), sort_keys=True))
