"""Build-time policy for Aster's self-contained installed runtime."""
import hashlib
import json
from pathlib import Path


ADDON = 'script.asterruntime'
INSTALL = '/storage/.kodi/addons/'+ADDON
COMPONENTS = (
    'aster-camera2',
    'aster-digest-player8', 'aster-digest-reader6',
    'aster-global-search-ui22', 'aster-home-status1',
    'aster-network-preview5', 'aster-series-preview24',
    'aster-video-scrub5',
)
SKIN_LAUNCHERS = (
    '1080i/Home.xml', '1080i/Settings.xml', '1080i/VideoOSD.xml',
    '1080i/custom_1111_digest.xml', '1080i/custom_1112_home.xml',
    'tools/aster_v2_digest.py', 'tools/aster_v2_series.py',
    'tools/header_search.py',
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def manifest_rows(component):
    """Return the accepted payload rows, supporting the early Home manifest."""
    value = json.loads((Path(component)/'manifest.json').read_text())
    rows = value.get('files')
    if isinstance(rows, dict):
        return [dict(path=name, sha256=value) for name, value in sorted(rows.items())]
    if not isinstance(rows, list):
        raise ValueError('family-runtime-component-manifest')
    return rows


def safe_relative(value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('family-runtime-relative-path')
    return path


def exact_members(component):
    component = Path(component)
    result = {}
    for row in manifest_rows(component):
        relative = safe_relative(row.get('path'))
        path = component/relative
        if path.is_symlink() or not path.is_file():
            raise ValueError('family-runtime-component-member')
        raw = path.read_bytes()
        if digest(raw) != row.get('sha256'):
            raise ValueError('family-runtime-component-drift')
        result[relative.as_posix()] = raw
    return result


def component_manifest(name, files, source_manifest_sha256, source_manifest=None):
    rows = [dict(path=path, bytes=len(raw), sha256=digest(raw))
            for path, raw in sorted(files.items())]
    value = dict(source_manifest or {})
    value.update(schema=1, component=name,
                 source_manifest_sha256=source_manifest_sha256, files=rows)
    return value
