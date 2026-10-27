"""Build the immutable v6 Network/Books Doctor diagnostics component."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from build_network_preview import layout


DOCTOR = r'''

def books_doctor(pin):
    verify(pin)
    sys.path.insert(0,str(ROOT))
    import epub_reader_doctor as reader
    sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
    import deploy_startup as guard
    if not guard.idle() or xbmcgui.getCurrentWindowId()!=10004:return

    class Doctor(xbmcgui.WindowXMLDialog):
        def onInit(self):
            self.identity=xbmcgui.getCurrentWindowDialogId();self.refresh=True
            self.setFocusId(1434);self.ready=True
        def onClick(self,n):
            if n==1434:self.refresh=True
            elif n==1435:self.finished=True;self.close()
        def onAction(self,a):
            if a.getId() in BACK:self.finished=True;self.close()
        def process(self):
            if not self.refresh:return
            self.refresh=False;self.getControl(1431).setLabel('Checking read-only publications…')
            self.getControl(1432).setText('');self.getControl(1433).setText('')
            value=reader.collect()
            self.getControl(1431).setLabel(value.state)
            self.getControl(1432).setText(value.summary)
            self.getControl(1433).setText('\n'.join(value.details))

    window=Doctor('BooksDoctor.xml',str(ROOT),'Default','1080i')
    window.identity=None;window.ready=False;window.finished=False;window.refresh=False
    window.show();monitor=xbmc.Monitor()
    try:
        for _ in range(80):
            if window.ready:break
            if monitor.waitForAbort(.05):return
        if not window.ready:raise ValueError('books-doctor-not-ready')
        while not window.finished and not monitor.waitForAbort(.1):
            if xbmcgui.getCurrentWindowDialogId()==window.identity:window.process()
            elif guard.idle():break
    finally:
        window.close();del window
'''


def replace_one(text, old, new, code):
    if text.count(old) != 1:
        raise ValueError(code)
    return text.replace(old, new)


def patch_default(raw):
    text = raw.decode('utf-8')
    text = replace_one(
        text,
        "MEMBERS={'default.py','network_diagnostics.py','network_service_checks.py',\n"
        "    'resources/skins/Default/1080i/NetworkPreview.xml',\n"
        "    'resources/skins/Default/1080i/DiagnosticsMenu.xml'}",
        "MEMBERS={'default.py','network_diagnostics.py','network_service_checks.py',\n"
        "    'epub_reader_doctor.py',\n"
        "    'resources/skins/Default/1080i/NetworkPreview.xml',\n"
        "    'resources/skins/Default/1080i/DiagnosticsMenu.xml',\n"
        "    'resources/skins/Default/1080i/BooksDoctor.xml'}",
        'network-doctor-members-anchor')
    text = replace_one(
        text,
        "value.get('kind')!='hp-network-preview.v5' or len(value['files'])!=5",
        "value.get('kind')!='hp-network-preview.v6' or len(value['files'])!=7",
        'network-doctor-contract-anchor')
    text = replace_one(
        text, "value.get('diagnostics_menu') is not True):",
        "value.get('diagnostics_menu') is not True or value.get('books_doctor') is not True or\n"
        "        value.get('repairs') is not False):",
        'network-doctor-flags-anchor')
    text = replace_one(text, 'if n in (1421,1422):self.choice=n',
                       'if n in (1421,1422,1423):self.choice=n',
                       'network-doctor-choice-anchor')
    text = replace_one(
        text,
        "        elif choice==1422 and xbmc.getCondVisibility('System.HasAddon(script.logviewer)'):\n"
        "            xbmc.executebuiltin('RunAddon(script.logviewer)')\n\n\ndef main():",
        "        elif choice==1422 and xbmc.getCondVisibility('System.HasAddon(script.logviewer)'):\n"
        "            xbmc.executebuiltin('RunAddon(script.logviewer)')\n"
        "        elif choice==1423:books_doctor(pin)\n" + DOCTOR + "\n\ndef main():",
        'network-doctor-handler-anchor')
    compile(text, 'default.py', 'exec')
    return text.encode('utf-8')


def menu_layout():
    root=ET.Element('window',type='dialog')
    ET.SubElement(root,'defaultcontrol',always='true').text='1421'
    controls=ET.SubElement(root,'controls')
    def node(kind,n,x,y,w,h,**values):
        c=ET.SubElement(controls,'control',dict(type=kind,**({'id':str(n)} if n else {})))
        for k,v in dict(left=x,top=y,width=w,height=h,**values).items():ET.SubElement(c,k).text=str(v)
        return c
    panel=node('image',None,1300,91,330,208)
    ET.SubElement(panel,'texture',border='18',colordiffuse='b0000000').text='special://skin/media/ui-panel.png'
    for n,y,label,up,down in ((1421,101,'Network status',1423,1422),
                              (1422,163,'View Kodi log',1421,1423),
                              (1423,225,'Books narration',1422,1421)):
        c=node('button',n,1312,y,306,62,label=label,font='font24',textcolor='fff3eee5',
            focusedcolor='fff3eee5',disabledcolor='ff96988f',align='left',aligny='center',
            textoffsetx='20',onup=up,ondown=down,onleft='noop',onright='noop')
        ET.SubElement(c,'texturefocus',border='18',colordiffuse='ff005c46').text='special://skin/media/ui-panel.png'
        ET.SubElement(c,'texturenofocus',border='18',colordiffuse='40000000').text='special://skin/media/ui-panel.png'
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'


def doctor_layout():
    root=ET.Element('window',type='dialog')
    ET.SubElement(root,'defaultcontrol',always='true').text='1434'
    controls=ET.SubElement(root,'controls')
    def node(kind,n,x,y,w,h,**values):
        c=ET.SubElement(controls,'control',dict(type=kind,**({'id':str(n)} if n else {})))
        for k,v in dict(left=x,top=y,width=w,height=h,**values).items():ET.SubElement(c,k).text=str(v)
        return c
    panel=node('image',None,1040,120,700,520)
    ET.SubElement(panel,'texture',border='24',colordiffuse='d8000000').text='special://skin/media/ui-panel.png'
    node('label',None,1080,155,620,50,label='Books narration',font='font32',textcolor='fff3eee5')
    node('label',1431,1080,225,620,42,label='Checking…',font='font24',textcolor='ffadccad')
    node('textbox',1432,1080,285,620,100,font='font24',textcolor='fff3eee5')
    node('textbox',1433,1080,405,620,115,font='font20',textcolor='ffc9cbc4')
    for n,x,w,label,other in ((1434,1080,250,'Refresh',1435),(1435,1360,250,'Back',1434)):
        c=node('button',n,x,550,w,58,label=label,font='font20',textcolor='fff3eee5',
               focusedcolor='fff3eee5',align='center',aligny='center',
               onleft=other,onright=other,onup='noop',ondown='noop')
        ET.SubElement(c,'texturefocus',border='18',colordiffuse='ff005c46').text='special://skin/media/ui-panel.png'
        ET.SubElement(c,'texturenofocus',border='18',colordiffuse='40000000').text='special://skin/media/ui-panel.png'
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'


def build(output):
    here=Path(__file__).resolve().parent;root=Path(output);root.mkdir(mode=0o700)
    files={'default.py':patch_default((here/'network_preview/default.py').read_bytes()),
        'network_diagnostics.py':(here/'network_diagnostics.py').read_bytes(),
        'network_service_checks.py':(here/'network_service_checks.py').read_bytes(),
        'epub_reader_doctor.py':(here/'epub_reader_doctor.py').read_bytes(),
        'resources/skins/Default/1080i/NetworkPreview.xml':layout(),
        'resources/skins/Default/1080i/DiagnosticsMenu.xml':menu_layout(),
        'resources/skins/Default/1080i/BooksDoctor.xml':doctor_layout()}
    rows=[]
    for name,raw in sorted(files.items()):
        path=root/name;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o600)
        rows.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    value=dict(kind='hp-network-preview.v6',normal_entry=False,network_probes=True,
        explicit_service_checks=True,diagnostics_menu=True,books_doctor=True,
        repairs=False,network_changes=False,files=rows)
    path=root/'manifest.json';path.write_text(json.dumps(value,indent=2)+'\n');path.chmod(0o600)
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    print(build(parser.parse_args().output))
