"""Compose a dialog/control-only search OK hook on accepted series dispatch."""
import ast,hashlib
import xml.etree.ElementTree as ET
BEFORE='0f44246aea2c0f7fbc716af3cdd8a591c766b356c4d257125175be48a7ab4548'
DETAILS_BEFORE='bdeed45b4fca9118f8bda98b75a6e6923d5ca5446a0940668b926f124441097d'
HOME_BEFORE='a45d2cea4d14e644d5211d2908ecd6f53aebff8a6467260fbb07539476a9f923'

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

def window_dispatcher(data):
    if hashlib.sha256(data).hexdigest()!=DETAILS_BEFORE:raise ValueError('unknown-details-dispatcher')
    needle='    if xbmcgui.getCurrentWindowDialogId() == 11127:\n'
    source=data.decode()
    if source.count(needle)!=1:raise ValueError('ambiguous-dialog-hook')
    result=source.replace(needle,'    if xbmcgui.getCurrentWindowId() == 11127 and xbmcgui.getCurrentWindowDialogId() in (0, 9999):\n')
    ast.parse(result);return result.encode()

def home_entry(data,stage):
    import re
    if hashlib.sha256(data).hexdigest()!=HOME_BEFORE:raise ValueError('unknown-home-predecessor')
    if not re.fullmatch(r'aster-global-search-ui(?:[5-9]|10|11|12)',stage):raise ValueError('unknown-handoff-stage')
    root=ET.fromstring(data)
    if root.find(".//control[@id='135']") is not None:raise ValueError('home-search-id-conflict')
    group=next(g for g in root.iter('control') if g.find("control[@id='134']") is not None)
    group.find("control[@id='134']/onright").text='135'
    button=ET.SubElement(group,'control',dict(type='button',id='135'))
    fields=dict(left=1620,top=31,width=110,height=46,label='Search',font='font20',align='center',aligny='center',
        textcolor='asterIvory',focusedcolor='asterInk',onleft=134,onright=134,onup=135,ondown=121,
        enable='!Player.HasMedia',onclick='RunScript(/storage/.aster-staging/'+stage+'/default.py)')
    for key,value in fields.items():ET.SubElement(button,key).text=str(value)
    for name,color in (('texturefocus','asterGold'),('texturenofocus','asterCharcoal')):
        ET.SubElement(button,name,dict(border='20',colordiffuse=color)).text='special://skin/media/ui-panel.png'
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)
