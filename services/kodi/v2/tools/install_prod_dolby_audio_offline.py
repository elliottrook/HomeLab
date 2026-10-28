"""Offline audio-only Kodi 22 edit; Kodi must be fully stopped."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

SETTINGS=Path('/storage/.kodi/userdata/guisettings.xml')
CHECKPOINT=Path('/storage/.aster-checkpoints/astertv-dolby-passthrough-offline-20261028')
EXPECTED={
    'audiooutput.audiodevice':'ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH',
    'audiooutput.passthroughdevice':'ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH',
    'audiooutput.passthrough':'false',
    'audiooutput.channels':'1',
    'audiooutput.config':'2',
    'audiooutput.ac3passthrough':'true',
    'audiooutput.eac3passthrough':'true',
    'audiooutput.truehdpassthrough':'true',
    'audiooutput.dtspassthrough':'true',
    'audiooutput.dtshdpassthrough':'true',
    'audiooutput.ac3transcode':'false',
}
CHANGES={
    'audiooutput.passthrough':'true',
    'audiooutput.channels':'10',
    'audiooutput.config':'3',
    'audiooutput.dtspassthrough':'false',
    'audiooutput.dtshdpassthrough':'false',
}
def values(raw):
    root=ET.fromstring(raw)
    rows={node.get('id'):node.text for node in root.iter('setting') if node.get('id') in EXPECTED}
    if set(rows)!=set(EXPECTED):raise RuntimeError('missing-audio-setting')
    return rows
def atomic(path,raw):
    fd,name=tempfile.mkstemp(prefix='.aster-audio-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(name,0o600)
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

if os.uname().nodename!='AsterTVProd':raise RuntimeError('production-only')
if subprocess.run(['systemctl','is-active','--quiet','kodi']).returncode==0:raise RuntimeError('kodi-running')
if not SETTINGS.is_file() or SETTINGS.is_symlink() or CHECKPOINT.exists():raise RuntimeError('file-boundary')
before=SETTINGS.read_bytes()
if values(before)!=EXPECTED:raise RuntimeError('audio-predecessor-changed')
after=before
for key,new in CHANGES.items():
    old=EXPECTED[key].encode()
    pattern=rb'<setting id="'+key.encode()+rb'"(?: default="true")?>'+old+rb'</setting>'
    after,count=re.subn(pattern,b'<setting id="'+key.encode()+b'">'+new.encode()+b'</setting>',after)
    if count!=1:raise RuntimeError('xml-predecessor:'+key)
target=dict(EXPECTED,**CHANGES)
if values(after)!=target:raise RuntimeError('xml-after-verification')
CHECKPOINT.mkdir(mode=0o700,parents=True)
(CHECKPOINT/'guisettings.xml.before').write_bytes(before)
(CHECKPOINT/'guisettings.xml.before').chmod(0o600)
(CHECKPOINT/'state.json').write_text('{"state":"prepared"}\n')
try:
    atomic(SETTINGS,after)
    if SETTINGS.read_bytes()!=after:raise RuntimeError('install-verification')
    (CHECKPOINT/'state.json').write_text('{"state":"installed"}\n')
except Exception:
    atomic(SETTINGS,before)
    (CHECKPOINT/'state.json').write_text('{"state":"rolled-back"}\n')
    raise
print(json.dumps(dict(installed=True,checkpoint=str(CHECKPOINT),before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),changed=list(CHANGES)),sort_keys=True))
