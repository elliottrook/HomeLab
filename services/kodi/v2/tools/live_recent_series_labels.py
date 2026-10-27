"""Read-only HP diagnostic for Home Recently Added item identity labels."""

import json, os, time
from pathlib import Path
import xbmc, xbmcgui

ROOT = Path('/storage/.aster-checkpoints/aster-series-latency1')
result = {'passed': False, 'window': xbmcgui.getCurrentWindowId(), 'items': []}
try:
    if os.uname().nodename != 'AsterTV' or result['window'] != 10000:
        raise RuntimeError('recent-labels-home-required')
    for index in range(10):
        xbmc.executebuiltin('SetFocus(110,' + str(index) + ',absolute)')
        xbmc.sleep(100)
        result['items'].append({
            'position': index,
            'label': xbmc.getInfoLabel('Container(110).ListItem.Label'),
            'dbtype': xbmc.getInfoLabel('Container(110).ListItem.DBTYPE'),
            'dbid': xbmc.getInfoLabel('Container(110).ListItem.DBID'),
            'aster_dbid': xbmc.getInfoLabel(
                'Container(110).ListItem.Property(AsterDbId)'),
            'kind': xbmc.getInfoLabel('Container(110).ListItem.Property(AsterMediaKind)'),
            'path': xbmc.getInfoLabel('Container(110).ListItem.Path'),
        })
    result['passed'] = bool(result['items'])
except Exception as error:
    result['code'] = str(error)
ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
path = ROOT / ('recent-labels-' + str(time.time_ns()) + '.json')
path.write_text(json.dumps(result, indent=2) + '\n'); path.chmod(0o600)
