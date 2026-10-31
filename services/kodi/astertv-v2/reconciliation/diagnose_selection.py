"""Log content-free selection identity for a bounded Kodi navigation test."""
import sys
import xbmc
import xbmcgui

container = int(sys.argv[1]) if len(sys.argv) == 2 and sys.argv[1].isdigit() else 0
kind = xbmc.getInfoLabel('Container(' + str(container) + ').ListItem.DBTYPE')
identity = xbmc.getInfoLabel('Container(' + str(container) + ').ListItem.DBID')
xbmc.log('AsterSelectionDiagnostic: ' + repr({
    'window': xbmcgui.getCurrentWindowId(), 'container': container,
    'kind': kind, 'valid_id': identity.isdecimal(),
    'focus': xbmcgui.Window(xbmcgui.getCurrentWindowId()).getFocusId()}), xbmc.LOGINFO)
