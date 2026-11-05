"""HP News explicit-click handoff; all other hub actions retain their old path."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

PLAYER = Path('/storage/.kodi/addons/script.asterruntime/aster-digest-player8')
PIN = '665dac7b6941e61d3b82c64393c4c344c32c0fa925fb2549139259b35b52009d'


def main(action):
    import os
    import xbmc
    import xbmcgui
    import xbmcvfs
    try:
        if os.uname().nodename not in ('AsterTV-Bedroom','AsterTV-Family','AsterTV-Jen') or action not in ('play', 'chapter'):
            raise ValueError('hp-news-action-required')
        raw = (PLAYER/'manifest.json').read_bytes()
        if hashlib.sha256(raw).hexdigest() != PIN: raise ValueError('player-stage-drift')
        for row in json.loads(raw)['files']:
            if hashlib.sha256((PLAYER/row['path']).read_bytes()).hexdigest() != row['sha256']:
                raise ValueError('player-member-drift')
        sys.path.insert(0, str(PLAYER/'resources/lib'))
        from digest_news_contract import request
        from digest_kodi_port import idle
        from digest_preview_source import read
        from digest_timeline import build_preview
        news_active = lambda: (xbmcgui.getCurrentWindowId() == 11111 or xbmc.getCondVisibility('Window.IsActive(1111)'))
        if not idle() or not news_active(): raise ValueError('idle-news-required')
        window = xbmcgui.Window(11111)
        focus = window.getFocusId()
        if window.getProperty('AsterHub.Ready') != 'true': raise ValueError('news-not-ready')
        generation = window.getProperty('AsterHub.GeneratedAt')
        position = ('0' if action == 'play' else xbmc.getInfoLabel('Container(500).ListItem.Property(AsterStart)'))
        args = ['news', 'full' if action == 'play' else 'story', position, generation]
        request(args, 11111)
        feed = read('/static/digest-audio/latest.json', 262144)
        data = json.loads(feed)
        build_preview(data, datetime.now(timezone.utc))
        if data['generated_at'] != generation: raise ValueError('news-edition-changed')
        # Preserve only the existing explicit-click, bounded briefing cache path.
        # This import defines functions; hub_data's __main__ block is not run.
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from hub_data import cached_digest_audio
        cached_digest_audio(xbmcvfs, generation)
        if (read('/static/digest-audio/latest.json', 262144) != feed or not idle()
                or not news_active() or window.getFocusId() != focus):
            raise ValueError('news-source-changed')
        window.setProperty('AsterHub.Status', 'Opening Aster briefing player')
        window.setProperty('AsterHub.RequestedStart', position if action == 'chapter' else '')
        window.setProperty('AsterHub.RequestedGeneration', generation if action == 'chapter' else '')
        xbmc.executebuiltin('RunScript('+str(PLAYER/'default.py')+','+','.join(args)+')')
    except (OSError, ValueError, KeyError, RuntimeError, TypeError):
        xbmcgui.Dialog().notification('Aster News', 'Briefing unavailable or changed. Refresh News and try again when idle.')
