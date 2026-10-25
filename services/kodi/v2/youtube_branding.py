"""Approved Aster YouTube selector; preserve the existing pill and its actions."""
import hashlib
import re
import xml.etree.ElementTree as ET

MASTER_SHA = '449f30b8ddff8b4fa3339bd58463064955a2215731766e2f724cd94ff611a3eb'
OLD = b'special://home/addons/plugin.video.youtube/resources/media/icon.png'
NEW = b'special://skin/media/33-aster-youtube-128.png'


def validate(data):
    if hashlib.sha256(data).hexdigest() != MASTER_SHA:
        raise ValueError('approved-master-drift')
    root = ET.fromstring(data)
    if root.get('viewBox') != '0 0 1254 1254': raise ValueError('approved-proportions')
    identifiers = set()
    refs = set()
    for node in root.iter():
        tag = node.tag.rsplit('}', 1)[-1]
        if tag in ('script', 'image', 'text', 'foreignObject', 'animate', 'set'):
            raise ValueError('non-vector-content')
        identity = node.get('id')
        if identity:
            if identity in identifiers: raise ValueError('duplicate-id')
            identifiers.add(identity)
        for key, value in node.attrib.items():
            key = key.rsplit('}', 1)[-1]
            if key.lower().startswith('on'): raise ValueError('event-handler')
            if key == 'href':
                if not value.startswith('#'): raise ValueError('external-reference')
                refs.add(value[1:])
            for match in re.findall(r'url\(([^)]+)\)', value):
                if not match.startswith('#'): raise ValueError('external-reference')
                refs.add(match[1:])
    if not refs <= identifiers: raise ValueError('missing-local-reference')
    return root


def replace_home(data):
    if data.count(OLD) != 1 or NEW in data:
        raise ValueError('one-original-youtube-icon-required')
    root = ET.fromstring(data)
    button = root.find(".//control[@id='136']")
    if button is None or button.findtext('label') != 'YouTube':
        raise ValueError('known-youtube-pill-required')
    result = data.replace(OLD, NEW)
    if ET.tostring(ET.fromstring(result).find(".//control[@id='136']")) != ET.tostring(button):
        raise ValueError('pill-changed')
    return result
