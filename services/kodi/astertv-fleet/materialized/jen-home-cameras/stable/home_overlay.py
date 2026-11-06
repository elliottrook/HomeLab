#!/usr/bin/env python3
"""Pure transforms for the Jen-only read-only Home/Cameras overlay."""

from __future__ import annotations

import copy
import hashlib
import json
import xml.etree.ElementTree as ET


PREDECESSOR_SHA256 = "ec3cae3a5bc7f2c687b2cd3d997947d3f2f76e195fb4b61243b1941db677266f"
CAMERA_WINDOW = 11134
DISPLAY_SUBJECT_PREFIX = "local:home-assistant:display:sha256:"


def _control(root, identity):
    rows = root.findall(".//control[@id='{}']".format(identity))
    if len(rows) != 1:
        raise ValueError("control-cardinality:{}:{}".format(identity, len(rows)))
    return rows[0]


def _replace_children(control, tag, values):
    for child in list(control):
        if child.tag == tag:
            control.remove(child)
    for value in values:
        ET.SubElement(control, tag).text = value


def transform_home(payload):
    # Git text fixtures end with one newline; the accepted live predecessor does not.
    payload = payload[:-1] if payload.endswith(b"\n") else payload
    if hashlib.sha256(payload).hexdigest() != PREDECESSOR_SHA256:
        raise ValueError("home-predecessor-drift")
    root = ET.fromstring(payload)
    for child in list(root):
        if child.tag in ("onload", "onunload") and "aster-camera2" in (child.text or ""):
            root.remove(child)
    top = _control(root, "308")
    _replace_children(top, "onclick", ["ActivateWindow({})".format(CAMERA_WINDOW)])
    _replace_children(top, "onright", ["309"])
    _replace_children(top, "ondown", ["302"])
    open_button = _control(root, "302")
    label = open_button.find("label")
    if label is None:
        raise ValueError("camera-button-label-missing")
    label.text = "Open cameras"
    _replace_children(open_button, "onclick", ["ActivateWindow({})".format(CAMERA_WINDOW)])
    _replace_children(open_button, "onup", ["308"])
    for node in root.findall(".//label"):
        if node.text == "$INFO[Window.Property(AsterHub.HomeCameraLabel)]":
            node.text = "Front of house"
        elif node.text == "$INFO[Window.Property(AsterHub.HomeCameraStatus)]":
            node.text = "Private · on-demand viewer"
    for image in root.findall(".//control[@type='image']"):
        texture = image.findtext("texture") or ""
        if "AsterHub.CameraImage" in texture:
            texture_node = image.find("texture")
            texture_node.text = "/storage/.aster-camera/camera-idle.png"
            texture_node.attrib.pop("background", None)
            visible = image.find("visible")
            if visible is not None:
                image.remove(visible)
            image.find("aspectratio").text = "keep"
    encoded = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    parsed = ET.fromstring(encoded)
    if len(parsed.findall(".//control[@id='308']/onclick")) != 1:
        raise ValueError("camera-top-route-invalid")
    if "aster-camera2" in encoded.decode():
        raise ValueError("home-retains-camera-runtime")
    return encoded


def display_subject(marker):
    if not isinstance(marker, bytes) or not marker or len(marker) > 4096:
        raise ValueError("display-marker-invalid")
    try:
        identity = json.loads(marker)
    except (UnicodeError, json.JSONDecodeError, TypeError) as error:
        raise ValueError("display-marker-invalid") from error
    if (not isinstance(identity, dict)
            or set(identity) != {"schema", "kind", "authority"}
            or identity.get("schema") != 1
            or identity.get("kind") != "astertv-home-display"
            or identity.get("authority") != "ha-home-dashboard-v4"):
        raise ValueError("display-marker-invalid")
    canonical = (json.dumps(identity, sort_keys=True) + "\n").encode()
    return DISPLAY_SUBJECT_PREFIX + hashlib.sha256(canonical).hexdigest()


def extend_registry(registry, subject):
    candidate = copy.deepcopy(registry)
    if not isinstance(subject, str) or not subject.startswith(DISPLAY_SUBJECT_PREFIX):
        raise ValueError("display-subject-invalid")
    profiles = candidate.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("profiles-invalid")
    admin = [row for row in profiles if row.get("id") == "jason" and row.get("role") == "recovery_admin"]
    if len(admin) != 1:
        raise ValueError("jason-recovery-admin-missing")
    row = admin[0]
    if any(item.get("service") == "home_assistant" for item in row.get("service_mappings", [])):
        raise ValueError("home-assistant-mapping-already-present")
    row["service_mappings"].append({"service": "home_assistant", "opaque_subject_id": subject, "enabled": True})
    row["entitlements"] = sorted(set(row.get("entitlements", [])) | {"home_status", "camera_view"})
    for guest in (item for item in profiles if item.get("role") == "guest"):
        if set(guest.get("entitlements", [])) & {"home_status", "camera_view", "home_control", "cameras"}:
            raise ValueError("guest-home-authority-present")
    return candidate
