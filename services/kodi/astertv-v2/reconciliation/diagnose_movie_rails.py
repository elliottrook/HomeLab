"""Log only bounded movie detail-rail counts and focus."""
import xbmc
import xbmcgui
w=xbmcgui.Window(11130)
def size(identity):
    try:return w.getControl(identity).size()
    except RuntimeError:return -1
xbmc.log('AsterMovieRailDiagnostic: '+repr({'window':xbmcgui.getCurrentWindowId(),
    'focus':w.getFocusId(),'cast':size(500),'related':size(501),
    'ready':w.getProperty('Movie.Ready')}),xbmc.LOGINFO)
