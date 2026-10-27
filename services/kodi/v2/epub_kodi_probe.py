#!/usr/bin/env python3
"""HP-only temporary probe for the bounded compiled EPUB playback test."""

import json
from pathlib import Path
import sys
import time

import xbmc
import xbmcgui


OUTPUT = Path('/tmp/aster-epub-kodi-probe.json')


def snapshot(label):
    home = xbmcgui.Window(10000)
    player = xbmc.Player()
    identity = home.getProperty('AsterBooksCompiler.Window')
    reader = xbmcgui.Window(int(identity)) if identity.isdigit() else None
    data = {
        'label': label,
        'window': xbmcgui.getCurrentWindowId(),
        'playing': player.isPlaying(),
        'playing_audio': player.isPlayingAudio(),
        'reader_window': identity,
        'reader_state': reader.getProperty('Books.State') if reader else '',
        'highlight_observed': reader.getProperty('Books.HighlightObserved') if reader else '',
    }
    temporary = OUTPUT.with_suffix('.new')
    temporary.write_text(json.dumps(data, sort_keys=True) + '\n')
    temporary.replace(OUTPUT)


mode = sys.argv[1] if len(sys.argv) == 2 else 'status'
if mode == 'play':
    identity = xbmcgui.Window(10000).getProperty('AsterBooksCompiler.Window')
    if not identity.isdigit():
        raise ValueError('probe-reader-window')
    xbmc.executebuiltin('SendClick(' + identity + ',201)')
    time.sleep(0.2)
elif mode == 'back':
    xbmc.executebuiltin('Action(Back)')
    time.sleep(0.2)
elif mode != 'status':
    raise ValueError('probe-mode')
snapshot(mode)
