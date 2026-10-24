"""Approved HP-only UI smoke test; requires the lab already open. No playback/queue writes."""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

from pathlib import Path
_require((Path("/etc/hostname").read_text().strip()=="AsterTV"), ("HP lab only"))
import codecs,json,socket,subprocess,time
def rpc(method,params=None):
    with socket.create_connection(('127.0.0.1',9090),timeout=20) as s:
        s.sendall((json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}})+'\n').encode());raw='';d=codecs.getincrementaldecoder('utf-8')()
        while True:
            part=s.recv(65536)
            if not part:raise RuntimeError('closed')
            raw+=d.decode(part)
            while raw.strip():
                raw=raw.lstrip()
                try:r,end=json.JSONDecoder().raw_decode(raw)
                except ValueError:break
                raw=raw[end:]
                if r.get('id')==1:
                    _require(('error' not in r), (r.get('error')))
                    return r['result']
def until(check,description,seconds=12):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():print('PASS',description,flush=True);return
        time.sleep(.1)
    raise AssertionError(description)
def focused(i):
    key=f'Control.HasFocus({i})'
    return rpc('XBMC.GetInfoBooleans',{'booleans':[key]})[key]
def action(name):rpc('Input.ExecuteAction',{'action':name})
def press(name,target=None):
    action(name)
    if target is not None:until(lambda:focused(target),'focus '+str(target))
def prop(name):
    window=rpc('XBMC.GetInfoLabels',{'labels':['Window(Home).Property(AsterV2Lab.Window)']})['Window(Home).Property(AsterV2Lab.Window)']
    _require((window.isdigit()), ('Launch the HP Music lab before testing'))
    key='Window('+window+').Property(Lab.'+name+')'
    return rpc('XBMC.GetInfoLabels',{'labels':[key]})[key]
def dispatch():subprocess.run(['kodi-send','--action=RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)'],check=True,stdout=subprocess.DEVNULL)
_require((not rpc('Player.GetActivePlayers')), ('native-check-failed'))
queue_before=rpc('Playlist.GetItems',{'playlistid':0})
until(lambda:focused(500),'initial genre focus')
press('right',501);press('right',502);press('right',503)
press('down',506);press('up',503)
press('left',502);press('left',501);press('left',500);press('left',9007);press('back',500)
press('right',501);press('right',502)
dispatch()
until(lambda:prop('Heading')=='Rock & Alternative / Albums' and focused(500),'G20 dispatcher opens genre Albums')
_require((prop('Count')=='283 albums'), ('native-check-failed'))
press('up',200);press('up',104);press('left',103);press('left',102);press('left',101)
dispatch()
until(lambda:prop('Heading')=='Rock & Alternative / Artists' and focused(500),'Artists category view')
_require((prop('Count')=='138 artists'), ('native-check-failed'))
press('right',501);press('right',502);press('right',503);press('right',300)
dispatch()
until(lambda:rpc('XBMC.GetInfoLabels',{'labels':['System.CurrentWindow']})['System.CurrentWindow'] in ('Keyboard','Virtual keyboard'),'search keyboard')
rpc('Input.SendText',{'text':'zz_no_match','done':True})
until(lambda:bool(prop('Empty')),'truthful empty search')
press('down',301);dispatch()
until(lambda:prop('Count')=='138 artists' and prop('Search')=='Search…','clear search restores artists')
press('back')
until(lambda:prop('View')=='genres' and focused(502),'Back restores same genre')
press('up',200);press('right',201);dispatch()
until(lambda:rpc('XBMC.GetInfoLabels',{'labels':['System.CurrentWindow']})['System.CurrentWindow'] in ('OK','OK dialog'),'shuffle preview dialog')
press('back')
until(lambda:prop('View')=='genres' and focused(201),'Back dismisses preview without leaving pilot')
press('down',502);press('right',503);press('right',300);press('down',301);press('down',302)
dispatch()
until(lambda:'progress' in rpc('XBMC.GetInfoLabels',{'labels':['System.CurrentWindow']})['System.CurrentWindow'].lower(),'refresh progress')
press('back')
until(lambda:'cancelled' in prop('Status').lower() and focused(302),'cancelled refresh retains previous catalogue')
_require((prop('Count')=='7 categories'), ('native-check-failed'))
dispatch()
until(lambda:prop('Status')=='Complete catalogue refreshed' and focused(302),'successful explicit refresh')
press('back')
until(lambda:rpc('XBMC.GetInfoLabels',{'labels':['System.CurrentWindow']})['System.CurrentWindow']=='Home','Back returns to ordinary Aster')
_require((not rpc('Player.GetActivePlayers')), ('native-check-failed'))
_require((rpc('Playlist.GetItems',{'playlistid':0})==queue_before), ('native-check-failed'))
print('PASS no playback or music queue change',flush=True)
