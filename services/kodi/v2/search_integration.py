"""Compose a dialog/control-only search OK hook on accepted series dispatch."""
import ast,hashlib
BEFORE='466b69269e56d8699838aabbe72ae533a580909603855850a047bf02e76d1a0e'

def dispatcher(data):
    if hashlib.sha256(data).hexdigest()!=BEFORE:raise ValueError('unknown-select-predecessor')
    source=data.decode();needle='    window_id = xbmcgui.getCurrentWindowId()\n'
    if source.count(needle)!=1:raise ValueError('ambiguous-select-source')
    hook=('    if xbmcgui.getCurrentWindowDialogId() == 11127:\n'
          '        try:\n'
          '            selected = xbmcgui.Window(11127).getFocusId() == 30\n'
          '        except RuntimeError:\n'
          '            selected = False\n'
          '        if selected and xbmcgui.Window(10000).getProperty("AsterSearch.Ready") == "true":\n'
          '            xbmc.executebuiltin("SetProperty(AsterSearch.Command,details,home)")\n'
          '            return\n')
    result=source.replace(needle,hook+needle);ast.parse(result);return result.encode()
