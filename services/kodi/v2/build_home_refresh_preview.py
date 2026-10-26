"""Immutable HP foreground-generation preview; normal Home remains unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from build_home_preview import layout


def build(output):
    here=Path(__file__).resolve().parent;root=Path(output)
    root.mkdir(mode=0o700)
    xml=ET.fromstring(layout())
    for node in xml.findall('.//control'):
        label=node.findtext('label') or ''
        if label.startswith('HP preview'):node.set('id','504')
        if label.startswith('Local-file preview'):
            node.set('id','505');node.find('top').text='991'
    controls=xml.find('.//control[@id="600"]')
    extra=ET.SubElement(controls,'control',type='label',id='506')
    for key,value in dict(left=100,top=1030,width=1720,height=30,font='font20',textcolor='ffadccad').items():
        ET.SubElement(extra,key).text=str(value)
    files={'default.py':(here/'home_refresh_preview/default.py').read_bytes(),
           'HomePreviewBase.py':(here/'home_preview/default.py').read_bytes(),
           'resources/skins/Default/1080i/HomePreview.xml':ET.tostring(xml,encoding='utf-8',xml_declaration=True)+b'\n'}
    for name in ('home_refresh.py','home_freshness.py','home_dashboard_model.py'):
        files['resources/lib/'+name]=(here/name).read_bytes()
    rows=[]
    for name,raw in sorted(files.items()):
        path=root/name;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        path.write_bytes(raw);path.chmod(0o600)
        rows.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    manifest=dict(kind='hp-home-refresh-preview.v1',normal_entry=False,network=False,
                  synthetic_fixture_support=True,files=rows)
    path=root/'manifest.json';path.write_text(json.dumps(manifest,indent=2)+'\n');path.chmod(0o600)
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    print(build(parser.parse_args().output))
