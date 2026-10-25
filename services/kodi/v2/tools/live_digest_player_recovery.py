"""One bounded recovery for the retired Digest player2 pilot audio only."""
import hashlib
import json
import os
from pathlib import Path
import time
import xbmc

if os.uname().nodename != 'AsterTV': raise RuntimeError('hp-only')
player = xbmc.Player()
result = dict(stopped=False)
if player.isPlayingAudio():
    expected = player.getPlayingFile()
    target = Path(expected)
    if (target.parent.parent != Path('/storage/.aster-checkpoints')
            or not target.parent.name.startswith('aster-digest-player-')
            or not target.name.startswith('session-') or target.suffix != '.mp3'):
        raise RuntimeError('not-private-player-trial')
    if hashlib.sha256((target.parent/'manifest.json').read_bytes()).hexdigest() != '9f0615078ad8923b75778978e4a144787f056d6f16ae8e2712da65bdc390425d':
        raise RuntimeError('not-retired-player2')
    if player.isPlayingAudio() and player.getPlayingFile() == expected:
        player.stop()
        end = time.monotonic()+8
        while player.isPlayingAudio() and player.getPlayingFile() == expected and time.monotonic() < end:
            xbmc.sleep(50)
        result['stopped'] = not player.isPlayingAudio()
    (target.parent/'recovery.json').write_text(json.dumps(result))
