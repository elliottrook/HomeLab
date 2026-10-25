"""Correct Settings captions to the skin's defined font20, retaining actions."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
from build_review3 import raw,sha,SKIN
from review2_ui import field,encoded
def build(previous,output,current=None):
    previous,output=Path(previous),Path(output)
    if output.exists():raise ValueError('immutable-output')
    source=Path(current) if current else previous/'payload'/SKIN/'1080i/Settings.xml';data=source.read_bytes();root=ET.fromstring(data)
    for font in root.iter('font'):
        if font.text=='font18':font.text='font20'
    for button in root.findall('.//control[@type="button"]'):
        if button.find('enable') is not None and button.get('id')!='139':field(button,'disabledcolor','ff96988f')
    after=encoded(root);output.mkdir();(output/'Settings.xml').write_bytes(after)
    (output/'manifest.json').write_bytes(raw(dict(member='Settings.xml',before_sha256=sha(data),sha256=sha(after))))
    return sha(data),sha(after)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--previous',required=True);p.add_argument('--output',required=True);p.add_argument('--current')
    a=p.parse_args();print(build(a.previous,a.output,a.current))
