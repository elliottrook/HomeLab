"""Shared anchored menu: no full-screen dimmer, no playback or server writes."""
from pathlib import Path
import xbmcgui

BACK={9,10,92,216,247,257,275}
class CompactMenu(xbmcgui.WindowXMLDialog):
    def onInit(self):
        height=min(7,len(self.labels))*48+66
        self.getControl(100).setPosition(self.left,max(20,min(self.top,1060-height)))
        self.getControl(101).setHeight(height)
        self.getControl(10).setHeight(height-66)
        self.setProperty('Compact.Title',self.title)
        listing=self.getControl(10);listing.reset()
        listing.addItems([xbmcgui.ListItem(label=label) for label in self.labels])
        listing.selectItem(max(0,min(self.selected,len(self.labels)-1)))
        self.setFocusId(10)
    def onClick(self,identity):
        if identity==10:
            self.result=self.getControl(10).getSelectedPosition();self.close()
    def onAction(self,action):
        if action.getId() in BACK:self.close()

def choose(title,labels,*,left=1110,top=430,selected=0):
    if not labels:return -1
    dialog=CompactMenu('CompactMenu.xml',str(Path(__file__).resolve().parents[1]),'Default','1080i')
    dialog.title=title;dialog.labels=list(labels);dialog.left=left;dialog.top=top
    dialog.selected=selected;dialog.result=-1
    dialog.doModal();result=dialog.result;del dialog
    return result
