"""Build the exact HP Jellyfin callback guard for a normal idle player."""
import ast
import hashlib
import json
from pathlib import Path


BEFORE = '21b93325b6ef9b50fdd3f5c48b273e12820f5a662ae534405dacdebcc15388fd'
NEEDLE = b'''    def get_playing_file(self):
        try:
            return self.getPlayingFile()
        except Exception as error:
            LOG.exception(error)
'''
REPLACEMENT = b'''    def get_playing_file(self):
        try:
            return self.getPlayingFile()
        except RuntimeError:
            # Kodi raises after a normal natural end, before late add-on
            # callbacks have drained. No current file is ordinary idle state.
            return None
        except Exception as error:
            LOG.exception(error)
'''


def digest(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return json.dumps(value, indent=2, sort_keys=True).encode()+b'\n'


def transform(raw, expected=None):
    expected = BEFORE if expected is None else expected
    if digest(raw) != expected or raw.count(NEEDLE) != 1:
        raise ValueError('jellyfin-idle-guard-predecessor')
    result = raw.replace(NEEDLE, REPLACEMENT)
    ast.parse(result)
    return result


def build(source, output):
    source, output = Path(source), Path(output)
    if output.exists(): raise ValueError('jellyfin-idle-guard-output-exists')
    raw = source.read_bytes(); result = transform(raw)
    output.mkdir(parents=True)
    (output/'player.py').write_bytes(result)
    manifest = dict(schema=1, kind='hp-jellyfin-idle-guard.v1',
        target='.kodi/addons/plugin.video.jellyfin/jellyfin_kodi/player.py',
        before_sha256=digest(raw), sha256=digest(result), bytes=len(result))
    (output/'manifest.json').write_bytes(encoded(manifest))
    return digest((output/'manifest.json').read_bytes())
