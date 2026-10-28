"""One-shot official add-on installer for the freshly reinstalled AsterTV lab."""

import os
import sys

import xbmc

ALLOWED = {
    'refresh': 'UpdateAddonRepos',
    'youtube': 'InstallAddon(plugin.video.youtube)',
    'inputstream': 'InstallAddon(inputstream.adaptive)',
    'dateutil': 'InstallAddon(script.module.dateutil)',
    'websocket': 'InstallAddon(script.module.websocket)',
    'typing': 'InstallAddon(script.module.typing_extensions)',
}

if os.uname().nodename != 'AsterTV' or len(sys.argv) != 2 or sys.argv[1] not in ALLOWED:
    raise RuntimeError('lab-bootstrap-boundary')

xbmc.executebuiltin(ALLOWED[sys.argv[1]])
xbmc.log('AsterLabBootstrap: submitted ' + sys.argv[1], xbmc.LOGINFO)
