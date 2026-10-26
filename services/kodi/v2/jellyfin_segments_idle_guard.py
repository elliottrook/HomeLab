"""Build the exact HP guard that skips segment checks for unmanaged media."""
import ast
import hashlib
import json
from pathlib import Path


BEFORE='303fec23128ad58163aca117901cb2f05d30b30eeb608220e3749634765e5203'
NEEDLE=b'''            if self.player.isPlaying() and settings("mediaSegmentsEnabled.bool"):
'''
REPLACEMENT=b'''            # Segment scanning belongs only to a positively owned Jellyfin item.
            # This also closes Kodi's natural-end race for unrelated local media.
            if (self.player.isPlaying() and self.player.played
                    and settings("mediaSegmentsEnabled.bool")):
'''


def digest(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return json.dumps(value,indent=2,sort_keys=True).encode()+b'\n'


def transform(raw,expected=None):
    expected=BEFORE if expected is None else expected
    if digest(raw)!=expected or raw.count(NEEDLE)!=1:
        raise ValueError('jellyfin-segments-predecessor')
    result=raw.replace(NEEDLE,REPLACEMENT); ast.parse(result); return result


def build(source,output):
    source,output=Path(source),Path(output)
    if output.exists(): raise ValueError('jellyfin-segments-output-exists')
    raw=source.read_bytes(); result=transform(raw); output.mkdir(parents=True)
    (output/'segments.py').write_bytes(result)
    manifest=dict(schema=1,kind='hp-jellyfin-segments-idle-guard.v1',
        target='.kodi/addons/plugin.video.jellyfin/jellyfin_kodi/segments.py',
        before_sha256=digest(raw),sha256=digest(result),bytes=len(result))
    (output/'manifest.json').write_bytes(encoded(manifest))
    return digest((output/'manifest.json').read_bytes())

