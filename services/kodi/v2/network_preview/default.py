"""HP local facts with explicit media checks; never changes network settings."""
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
from queue import SimpleQueue,Empty
import re
import sys
import time
import xbmc
import xbmcgui

ROOT=Path(__file__).resolve().parent
MEMBERS={'default.py','network_diagnostics.py','network_service_checks.py',
    'resources/skins/Default/1080i/NetworkPreview.xml',
    'resources/skins/Default/1080i/DiagnosticsMenu.xml'}
BACK={9,10,92,216,247,257,275}


def verify(pin):
    if not re.fullmatch('[0-9a-f]{64}',pin):raise ValueError('network-preview-pin')
    raw=(ROOT/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('network-preview-manifest')
    value=json.loads(raw)
    if (value.get('kind')!='hp-network-preview.v5' or len(value['files'])!=5
        or {r['path'] for r in value['files']}!=MEMBERS or
        any(value.get(k) is not False for k in ('normal_entry','network_changes')) or
        value.get('network_probes') is not True or value.get('explicit_service_checks') is not True or
        value.get('diagnostics_menu') is not True):
        raise ValueError('network-preview-contract')
    for row in value['files']:
        path=ROOT/row['path']
        if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('network-preview-linked')
        raw=path.read_bytes()
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('network-preview-member')


def display_lines(values,empty):
    return '\n'.join(values[:4])+('\n'+str(len(values)-4)+' more configured entries' if len(values)>4 else '') if values else empty


def run(pin,demo):
    verify(pin)
    sys.path.insert(0,str(ROOT))
    import network_diagnostics as network
    import network_service_checks as services
    sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
    import deploy_startup as guard
    source=xbmcgui.getCurrentWindowId()
    if not guard.idle() or source not in (10000,10004):return
    home=xbmcgui.Window(10000);source_focus=xbmc.getInfoLabel('System.CurrentControlId')

    class NetworkPreview(xbmcgui.WindowXML):
        def onInit(self):
            self.identity=xbmcgui.getCurrentWindowId();self.revision=0;self.service_revision=0
            self.check_services=False
            self.setProperty('NetworkPreview.ServiceRevision','0')
            self.getControl(504).setLabel('Offline demonstration · network settings were NOT changed' if demo
                else 'Local facts · optional checks of two named private media endpoints · no sign-in or playback test')
            self.getControl(501).setLabel('Reading local configuration…')
            self.setFocusId(200);self.refresh=True
            self.getControl(203).setEnabled(False)
            home.setProperty('AsterNetwork.PreviewWindow',str(self.identity))

        def onClick(self,n):self.commands.put(('click',n))
        def onAction(self,a):
            if a.getId() in BACK:self.commands.put(('back',None))

        def process(self):
            for _ in range(16):
                try:kind,n=self.commands.get_nowait()
                except Empty:break
                if kind=='back' or n==201:
                    if guard.idle():self.return_source=True;self.finished=True;self.close()
                elif n==200:self.refresh=True;self.check_services=False
                elif n==203 and not demo:self.check_services=True
            if self.finished:return
            if self.refresh:self.render_facts()
            elif self.check_services:self.render_services()

        def render_facts(self):
            self.refresh=False;self.setProperty('NetworkPreview.Ready','false')
            self.getControl(501).setLabel('Reading local configuration…');self.repaint()
            facts=network.model('', 'Iface Destination Gateway Flags RefCnt Use Metric Mask MTU Window IRTT\n',
                '',{},datetime.now(timezone.utc)) if demo else network.collect()
            if xbmcgui.getCurrentWindowId()!=self.identity:return
            self.getControl(501).setLabel(facts.state)
            self.getControl(502).setLabel('Interface: '+(facts.interface or 'Not identified')+' · Link: '+facts.link.title())
            self.getControl(511).setText(display_lines([address+' · '+interface for interface,address in facts.addresses],
                'No non-loopback IPv4 address is currently assigned.'))
            self.getControl(512).setText(facts.gateway or 'No unambiguous gateway address is configured.')
            self.getControl(513).setText(display_lines(list(facts.dns),'No configured DNS server was found.'))
            self.getControl(514).setText('\n'.join(facts.notes))
            self.facts_notes=facts.notes
            self.getControl(505).setLabel('Reachability: '+facts.reachability+' · Refreshed '+facts.observed_at)
            self.getControl(516).setText('Disabled in offline demonstration.' if demo else
                'Not tested · select Check media services to send two private HTTP requests.')
            self.getControl(203).setEnabled(not demo)
            self.setProperty('NetworkPreview.ServiceRequests','0')
            self.setProperty('NetworkPreview.ServiceStatus','not-tested')
            for i in range(2):self.setProperty('NetworkPreview.ServiceHTTP'+str(i),'none')
            self.revision+=1
            self.setProperty('NetworkPreview.State',facts.state)
            self.setProperty('NetworkPreview.Revision',str(self.revision))
            self.setProperty('NetworkPreview.Reachability',facts.reachability)
            self.setProperty('NetworkPreview.Ready','true');self.repaint()

        def render_services(self):
            self.check_services=False
            if demo:return
            self.getControl(516).setText('Checking two named private endpoints…');self.repaint()
            results=services.check_all(lambda:xbmcgui.getCurrentWindowId()==self.identity
                and guard.idle() and self.commands.empty())
            if xbmcgui.getCurrentWindowId()!=self.identity:return
            found={r.name:r for r in results};rows=[]
            for name in services.ENDPOINTS:
                value=found.get(name)
                rows.append(name+' · '+(value.state+(' · HTTP '+str(value.status) if value.status is not None else '')
                    +' · '+str(value.elapsed_ms)+' ms' if value else 'Not checked; cancelled'))
            self.getControl(516).setText('\n'.join(rows))
            self.getControl(514).setText('\n'.join(self.facts_notes[:-1]+(
                'HTTP responses only; DNS, Internet, sign-in and playback remain untested.',)))
            self.getControl(505).setLabel('Media endpoint responses only · DNS/gateway/Internet not tested · Checked '+
                datetime.now(timezone.utc).strftime('%H:%M:%S UTC'))
            self.service_revision+=1
            self.setProperty('NetworkPreview.ServiceRevision',str(self.service_revision))
            self.setProperty('NetworkPreview.ServiceRequests',str(len(results)))
            for i,name in enumerate(services.ENDPOINTS):
                value=found.get(name)
                self.setProperty('NetworkPreview.ServiceHTTP'+str(i),
                    str(value.status) if value and value.status is not None else 'none')
            self.setProperty('NetworkPreview.ServiceStatus','complete' if len(results)==2 else 'cancelled')
            self.setProperty('NetworkPreview.Reachability','Only media HTTP endpoints checked')
            self.repaint()

        def repaint(self):
            self.setProperty('NetworkPreview.Paint','odd' if getattr(self,'paint',False) else 'even')
            self.paint=not getattr(self,'paint',False)

    window=NetworkPreview('NetworkPreview.xml',str(ROOT),'Default','1080i')
    window.identity=None;window.finished=False;window.return_source=False;window.commands=SimpleQueue();window.refresh=False
    window.show();monitor=xbmc.Monitor()
    try:
        for _ in range(80):
            if window.identity is not None:break
            if monitor.waitForAbort(.05):return
        if window.identity is None:raise ValueError('network-preview-not-ready')
        while not window.finished and not monitor.waitForAbort(.1):
            if xbmcgui.getCurrentWindowId()==window.identity:window.process()
            elif guard.idle():break
    finally:
        window.close();home.clearProperty('AsterNetwork.PreviewWindow')
        if window.return_source and source==10004 and guard.idle() and xbmcgui.getCurrentWindowId()==10000:
            xbmc.executebuiltin('ActivateWindow(Settings)')
        for _ in range(20):
            if xbmcgui.getCurrentWindowId()==source:break
            xbmc.sleep(50)
        if guard.idle() and xbmcgui.getCurrentWindowId()==source and source_focus.isdigit():
            xbmc.executebuiltin('Control.SetFocus('+str(source_focus)+')')
        del window


def diagnostics(pin):
    verify(pin)
    sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
    import deploy_startup as guard
    if not guard.idle() or xbmcgui.getCurrentWindowId()!=10004:return
    home=xbmcgui.Window(10000)

    class Menu(xbmcgui.WindowXMLDialog):
        def onInit(self):
            self.identity=xbmcgui.getCurrentWindowDialogId()
            has_logs=xbmc.getCondVisibility('System.HasAddon(script.logviewer)')
            self.getControl(1422).setEnabled(has_logs)
            if not has_logs:self.getControl(1422).setLabel('Log not installed')
            self.setFocusId(1421);self.ready=True
            home.setProperty('AsterNetwork.MenuOpen',str(self.identity))
        def onClick(self,n):
            if n in (1421,1422):self.choice=n;self.finished=True;self.close()
        def onAction(self,a):
            if a.getId() in BACK:self.finished=True;self.close()

    menu=Menu('DiagnosticsMenu.xml',str(ROOT),'Default','1080i')
    menu.identity=None;menu.choice=None;menu.ready=False;menu.finished=False
    menu.show();monitor=xbmc.Monitor()
    try:
        for _ in range(80):
            if menu.ready:break
            if monitor.waitForAbort(.05):return
        if not menu.ready:raise ValueError('network-menu-not-ready')
        while not menu.finished and not monitor.waitForAbort(.1):
            if (xbmcgui.getCurrentWindowId()!=10004 or
                xbmcgui.getCurrentWindowDialogId()!=menu.identity) and guard.idle():break
    finally:
        choice=menu.choice;menu.close();home.clearProperty('AsterNetwork.MenuOpen')
        for _ in range(20):
            if xbmcgui.getCurrentWindowDialogId()!=menu.identity:break
            xbmc.sleep(50)
        del menu
    if guard.idle() and xbmcgui.getCurrentWindowId()==10004:
        xbmc.executebuiltin('Control.SetFocus(206)')
        if choice==1421:run(pin,False)
        elif choice==1422 and xbmc.getCondVisibility('System.HasAddon(script.logviewer)'):
            xbmc.executebuiltin('RunAddon(script.logviewer)')


def main():
    if os.uname().nodename!='AsterTV':return
    lock=None
    try:
        if len(sys.argv) not in (2,3) or (len(sys.argv)==3 and sys.argv[2] not in ('offline-demo','diagnostics')):
            raise ValueError('network-preview-arguments')
        verify(sys.argv[1])
        lock=os.open(str(ROOT/'entry.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if len(sys.argv)==3 and sys.argv[2]=='diagnostics':diagnostics(sys.argv[1])
        else:run(sys.argv[1],len(sys.argv)==3)
    except (OSError,ValueError,KeyError,TypeError,RuntimeError):
        xbmcgui.Dialog().notification('Aster Network','Local diagnostics unavailable. No network settings were changed.')
    finally:
        if lock is not None:os.close(lock)


if __name__=='__main__':main()
