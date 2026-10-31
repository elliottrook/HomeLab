"""Content-free Aster custom-window diagnostic for Kodi 22."""

import sys

import xbmc
import xbmcgui


window_id = int(sys.argv[1]) if len(sys.argv) == 2 and sys.argv[1].isdigit() else 0
try:
    focus = xbmcgui.Window(window_id).getFocusId() if window_id else 0
except RuntimeError:
    focus = 0
window = xbmcgui.Window(window_id) if window_id else None
fields = {
    "reported": xbmcgui.getCurrentWindowId(),
    "dialog": xbmcgui.getCurrentWindowDialogId(),
    "target": window_id,
    "active": bool(window_id and xbmc.getCondVisibility("Window.IsActive(" + str(window_id) + ")")),
    "visible": bool(window_id and xbmc.getCondVisibility("Window.IsVisible(" + str(window_id) + ")")),
    "focus": focus,
    "focus312": xbmc.getCondVisibility("Control.HasFocus(312)"),
    "ready": bool(window and window.getProperty("AsterHub.Ready") == "true"),
    "rows": bool(window and window.getProperty("AsterHub.RowsReady") == "true"),
    "generated": window.getProperty("AsterHub.GeneratedAt") if window else "",
    "status": window.getProperty("AsterHub.Status") if window else "",
}
xbmc.log("AsterWindowDiagnostic: " + repr(fields), xbmc.LOGINFO)
