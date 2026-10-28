"""Restore the known-good TV stereo route after exact runtime checks."""
import json
from pathlib import Path
import shutil
import xbmc

CHECKPOINT=Path('/storage/.aster-checkpoints/astertv-tv-audio-20261028')
SETTINGS=Path('/storage/.kodi/userdata/guisettings.xml')
BEFORE={
    'audiooutput.audiodevice':'ALSA:@:CARD=PCH,DEV=0|HDA Intel PCH',
    'audiooutput.passthroughdevice':'ALSA:hdmi:CARD=PCH,DEV=1|HDA Intel PCH',
    'audiooutput.passthrough':True,
    'audiooutput.channels':10,
    'audiooutput.config':3,
}
AFTER={
    'audiooutput.audiodevice':'ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH',
    'audiooutput.passthroughdevice':'ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH',
    'audiooutput.passthrough':False,
    'audiooutput.channels':1,
    'audiooutput.config':2,
}
def rpc(method,params=None):
    response=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in response:raise RuntimeError('rpc:'+method+':'+response['error'].get('message','unknown'))
    return response['result']
def value(key):return rpc('Settings.GetSettingValue',{'setting':key})['value']
if rpc('Player.GetActivePlayers'):raise RuntimeError('active-player')
if CHECKPOINT.exists():raise RuntimeError('checkpoint-exists')
if {key:value(key) for key in BEFORE}!=BEFORE:raise RuntimeError('audio-predecessor-changed')
if not SETTINGS.is_file() or SETTINGS.is_symlink():raise RuntimeError('settings-file-boundary')
CHECKPOINT.mkdir(mode=0o700,parents=True)
shutil.copyfile(SETTINGS,CHECKPOINT/'guisettings.xml.before')
(CHECKPOINT/'guisettings.xml.before').chmod(0o600)
(CHECKPOINT/'runtime-before.json').write_text(json.dumps(BEFORE,sort_keys=True)+'\n')
(CHECKPOINT/'runtime-before.json').chmod(0o600)
(CHECKPOINT/'state.json').write_text('{"state":"prepared"}\n')
try:
    for key in ('audiooutput.passthrough','audiooutput.audiodevice','audiooutput.passthroughdevice',
                'audiooutput.channels','audiooutput.config'):
        rpc('Settings.SetSettingValue',{'setting':key,'value':AFTER[key]})
    if {key:value(key) for key in AFTER}!=AFTER:raise RuntimeError('audio-verification')
    (CHECKPOINT/'state.json').write_text('{"state":"installed"}\n')
except Exception:
    for key in ('audiooutput.passthrough','audiooutput.audiodevice','audiooutput.passthroughdevice',
                'audiooutput.channels','audiooutput.config'):
        rpc('Settings.SetSettingValue',{'setting':key,'value':BEFORE[key]})
    (CHECKPOINT/'state.json').write_text('{"state":"rolled-back"}\n')
    raise
Path('/tmp/astertv-prod-audio-repair-result.json').write_text(json.dumps(dict(installed=True,route='Beyond TV HDMI 0',passthrough=False,channels='stereo',checkpoint=str(CHECKPOINT)))+'\n')
