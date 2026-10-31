"""Transiently verify movie detail ControlList population, without content."""
import xbmc
import xbmcgui
w=xbmcgui.Window(11130);result={}
for identity in (500,501):
    control=w.getControl(identity);before=control.size();item=xbmcgui.ListItem(label='Diagnostic')
    control.addItems([item]);after=control.size();control.reset();result[identity]=(before,after,control.size())
xbmc.log('AsterMovieControlDiagnostic: '+repr(result),xbmc.LOGINFO)
