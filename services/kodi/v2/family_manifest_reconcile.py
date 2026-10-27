"""Build an exact metadata successor for one accepted HP Home.xml change."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


HOME = '1080i/Home.xml'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, indent=2, sort_keys=True).encode() + b'\n'


def build(addon, skin, output):
    addon, skin, output = Path(addon), Path(skin), Path(output)
    if output.exists():
        raise ValueError('family-reconcile-output-exists')
    source_path = addon/'family-manifest.json'
    if source_path.is_symlink() or not source_path.is_file():
        raise ValueError('family-reconcile-source')
    source_raw = source_path.read_bytes()
    family = json.loads(source_raw)
    if family.get('kind') != 'aster-family-runtime.v1':
        raise ValueError('family-reconcile-kind')
    mismatches = []
    for name, info in family.get('components', {}).items():
        path = addon/name/'manifest.json'
        if (path.is_symlink() or not path.is_file()
                or digest(path.read_bytes()) != info.get('manifest_sha256')):
            mismatches.append('component:'+name)
    for name, expected in family.get('skin', {}).items():
        path = skin/name
        if (path.is_symlink() or not path.is_file()
                or digest(path.read_bytes()) != expected):
            mismatches.append('skin:'+name)
    if mismatches != ['skin:'+HOME]:
        raise ValueError('family-reconcile-unexpected-drift:'+','.join(mismatches))
    home = (skin/HOME).read_bytes()
    ET.fromstring(home)
    family['skin'][HOME] = digest(home)
    replacement = encoded(family)
    output.mkdir(parents=True)
    (output/'family-manifest.json').write_bytes(replacement)
    manifest = dict(schema=1, kind='hp-family-manifest-reconcile.v1',
        target='script.asterruntime/family-manifest.json',
        before_sha256=digest(source_raw), home_sha256=digest(home),
        sha256=digest(replacement), bytes=len(replacement))
    (output/'manifest.json').write_bytes(encoded(manifest))
    return digest((output/'manifest.json').read_bytes())


def build_successor(source, home, output, helper=None, deploy=None):
    """Build a successor from two exact, separately captured live files.

    The installer independently proves that Home is the only drift from the
    predecessor before it creates a checkpoint or changes the live manifest.
    This smaller input surface avoids copying an entire active add-on tree into
    the build workspace merely to advance one integrity hash.
    """
    source, home, output = Path(source), Path(home), Path(output)
    helper = Path(helper) if helper else Path(__file__).with_name(
        'family_manifest_reconcile_install.py')
    deploy = Path(deploy) if deploy else Path(__file__).with_name(
        'tools')/'deploy_family_manifest_reconcile2.py'
    if output.exists():
        raise ValueError('family-reconcile-output-exists')
    if source.is_symlink() or not source.is_file():
        raise ValueError('family-reconcile-source')
    if home.is_symlink() or not home.is_file():
        raise ValueError('family-reconcile-home')
    if (helper.is_symlink() or not helper.is_file()
            or deploy.is_symlink() or not deploy.is_file()):
        raise ValueError('family-reconcile-tools')
    source_raw, home_raw = source.read_bytes(), home.read_bytes()
    family = json.loads(source_raw)
    if (family.get('kind') != 'aster-family-runtime.v1'
            or HOME not in family.get('skin', {})):
        raise ValueError('family-reconcile-kind')
    ET.fromstring(home_raw)
    home_sha = digest(home_raw)
    if family['skin'][HOME] == home_sha:
        raise ValueError('family-reconcile-home-not-drifted')
    family['skin'][HOME] = home_sha
    replacement = encoded(family)
    output.mkdir(parents=True)
    (output/'family-manifest.json').write_bytes(replacement)
    helper_raw, deploy_raw = helper.read_bytes(), deploy.read_bytes()
    (output/'family_manifest_reconcile_install.py').write_bytes(helper_raw)
    (output/'deploy_family_manifest_reconcile2.py').write_bytes(deploy_raw)
    manifest = dict(schema=1, kind='hp-family-manifest-reconcile.v2',
        target='script.asterruntime/family-manifest.json',
        before_sha256=digest(source_raw), home_sha256=home_sha,
        sha256=digest(replacement), bytes=len(replacement),
        helper_sha256=digest(helper_raw), deploy_sha256=digest(deploy_raw))
    (output/'manifest.json').write_bytes(encoded(manifest))
    return digest((output/'manifest.json').read_bytes())
