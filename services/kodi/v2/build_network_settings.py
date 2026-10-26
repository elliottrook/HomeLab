"""Generate a one-action Settings overlay from its exact accepted predecessor."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from network_settings_install import TARGET,BEFORE,NETWORK,NETWORK_PIN

def patch_page(raw):
    if hashlib.sha256(raw).hexdigest()!=BEFORE:raise ValueError('exact-network-settings-page-required')
    root=ET.fromstring(raw);button=root.find(".//control[@id='206']")
    if button.findtext('onclick')!='RunAddon(script.logviewer)':raise ValueError('exact-network-settings-action')
    button.find('onclick').text='RunScript(/storage/.aster-staging/'+NETWORK+'/default.py,'+NETWORK_PIN+',diagnostics)'
    button.find('enable').text='!Player.HasMedia'
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'

def build(output,source):
    here=Path(__file__).resolve().parent;root=Path(output);root.mkdir(mode=0o700)
    raw=patch_page(Path(source).read_bytes());path=root/'payload'/TARGET
    path.parent.mkdir(parents=True,mode=0o700);path.write_bytes(raw);path.chmod(0o600)
    helpers={}
    for name in ('network_settings_install.py','digest_news_install.py','deploy_network_settings.py'):
        data=(here/name if name!='deploy_network_settings.py' else here/'tools'/name).read_bytes()
        (root/name).write_bytes(data);(root/name).chmod(0o600);helpers[name]=hashlib.sha256(data).hexdigest()
    m=dict(kind='hp-network-settings.v1',network_manifest_sha256=NETWORK_PIN,
        files=[dict(path=TARGET,before_sha256=BEFORE,sha256=hashlib.sha256(raw).hexdigest())],helpers=helpers)
    path=root/'manifest.json';path.write_text(json.dumps(m,indent=2)+'\n');path.chmod(0o600)
    return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--source',required=True)
    a=p.parse_args();print(build(a.output,a.source))
