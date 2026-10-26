"""Build the three-file normal Home adapter overlay; preserve shared helpers."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from review2_ui import field,encoded

def main():
    source,destination=map(Path,sys.argv[1:])
    data=source.read_bytes();root=ET.fromstring(data)
    if root.findtext('onload')!='RunScript(special://skin/tools/hub_data.py,home)':raise ValueError('home-status-source')
    destination.mkdir(mode=0o700,exist_ok=False,parents=True)
    action='RunScript(/storage/.aster-staging/aster-home-status1/default.py,'
    field(root,'onload',action+'entry)');field(root,'onunload',action+'leave)')
    for identity,mode in ((300,'refresh'),(301,'overview'),(307,'lighting')):
        field(root.find(f'.//control[@id="{identity}"]'),'onclick',action+mode+')')
    for node in root.iter('control'):
        if node.findtext('label')=='Household':field(node,'label','$INFO[Window.Property(AsterHub.HomeSection)]')
        if node.findtext('label')=='Read-only Home Assistant status':
            field(node,'label','$INFO[Window.Property(AsterHub.HomeSourceNotice)]');field(node,'font','font16')
    (destination/'custom_1112_home.xml').write_bytes(encoded(root))
    shutil.copyfile(Path(__file__).resolve().parents[1]/'home_status_page.py',destination/'default.py')
    shutil.copyfile(Path(__file__).resolve().parents[1]/'home_status_model.py',destination/'home_status_model.py')
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.iterdir()}
    manifest=dict(kind='home-status-1',predecessor=hashlib.sha256(data).hexdigest(),files=files)
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(files=len(files),manifest=hashlib.sha256((destination/'manifest.json').read_bytes()).hexdigest())))

if __name__=='__main__':main()
