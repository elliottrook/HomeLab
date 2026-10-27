"""Two-host camera payload; private credentials/frames never enter the build."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from review2_ui import field,encoded

UNIT='''[Unit]
Description=Aster HP private on-demand camera viewer
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=3
[Service]
Type=simple
ExecStart=/usr/bin/python3 -B /storage/.aster-camera/proxy.py
WorkingDirectory=/storage/.aster-camera
Restart=on-failure
RestartSec=5
TimeoutStopSec=3
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
CapabilityBoundingSet=
RestrictAddressFamilies=AF_INET AF_UNIX
MemoryMax=96M
TasksMax=16
CPUQuota=25%
Nice=5
[Install]
WantedBy=multi-user.target
'''
ICON='''<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 96 96"><g fill="none" stroke="#accbda" stroke-width="2.4" stroke-linejoin="round"><path d="M17 30 H30 L35 22 H61 L66 30 H79 Q85 30 85 37 V70 Q85 77 78 77 H18 Q11 77 11 70 V37 Q11 30 17 30Z"/><circle cx="48" cy="52" r="16"/><circle cx="48" cy="52" r="10" stroke="#c1ad7c" stroke-opacity=".8"/><path d="M71 39 H76" stroke-linecap="round"/></g></svg>'''

def main():
    source,destination=map(Path,sys.argv[1:]);base=Path(__file__).resolve().parents[1]
    destination.mkdir(mode=0o700,parents=True,exist_ok=False)
    for name,original in (('frame.py','camera_source.py'),('proxy.py','camera_proxy.py'),('view.py','camera_page.py')):
        shutil.copyfile(base/original,destination/name)
    (destination/'aster-camera.service').write_text(UNIT);(destination/'camera-idle.svg').write_text(ICON)
    node=os.environ.get('ASTER_NODE','/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
    sharp=os.environ.get('ASTER_SHARP','/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')
    subprocess.run([node,'-e',"require(process.argv[1])(Buffer.from(process.argv[2])).png().toFile(process.argv[3])",sharp,ICON,str(destination/'camera-idle.png')],check=True)
    raw=source.read_bytes();root=ET.fromstring(raw)
    field(root,'onload','RunScript(/storage/.aster-camera/view.py,entry)')
    field(root,'onunload','RunScript(/storage/.aster-camera/view.py,leave)')
    button=root.find('.//control[@id="302"]');field(button,'onclick','RunScript(/storage/.aster-camera/view.py,toggle)')
    field(button,'label','$INFO[Window.Property(AsterHub.CameraButtonLabel)]')
    for image in root.findall('.//control[@type="image"]'):
        if image.findtext('texture')=='special://skin/media/aster-compass-128.png':
            for key,value in dict(left=875,top=598,width=120,height=120,texture='/storage/.aster-camera/camera-idle.png',colordiffuse='b0ffffff').items():field(image,key,value)
    (destination/'custom_1112_home.xml').write_bytes(encoded(root))
    members={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.iterdir() if p.suffix!='.svg'}
    (destination/'manifest.json').write_text(json.dumps(dict(kind='hp-one-camera-v1',predecessor=hashlib.sha256(raw).hexdigest(),files=members),sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(files=len(members),manifest=hashlib.sha256((destination/'manifest.json').read_bytes()).hexdigest())))

if __name__=='__main__':main()
