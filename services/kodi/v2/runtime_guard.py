"""Small read-only Kodi state guard shared by installed Aster pages."""
import hashlib
import json
from pathlib import Path

import xbmc


NAV = Path('/storage/.kodi/addons/resource.uisounds.asterhome/resources')


def _rpc(method, params=None):
    if method not in ('Player.GetActivePlayers', 'Playlist.GetItems',
                      'Settings.GetSettings'):
        raise RuntimeError('runtime-guard-rpc-boundary')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(
        jsonrpc='2.0', id=1, method=method, params=params or {}))))
    if 'error' in reply:
        raise RuntimeError('runtime-guard-rpc')
    return reply['result']


def idle():
    return not _rpc('Player.GetActivePlayers') and all(
        _rpc('Playlist.GetItems', dict(playlistid=value,
             limits=dict(start=0, end=1)))['limits']['total'] == 0
        for value in (0, 1))


def snapshot():
    settings = _rpc('Settings.GetSettings')['settings']
    settings_hash = hashlib.sha256(json.dumps(
        settings, sort_keys=True).encode()).hexdigest()
    navigation = {}
    if NAV.is_dir() and not NAV.is_symlink():
        for path in NAV.iterdir():
            if path.is_file() and not path.is_symlink() and path.suffix in ('.xml', '.wav'):
                navigation[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(settings_sha256=settings_hash, navigation=navigation)
