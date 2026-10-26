"""Generate only a pinned News rail successor from the exact accepted XML."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from digest_read_news_install import TARGET, BEFORE, READER, READER_PIN


def patch_page(raw):
    if hashlib.sha256(raw).hexdigest()!=BEFORE: raise ValueError('exact-read-news-page-required')
    root = ET.fromstring(raw)
    group = root.find("./controls/control[@type='group']")
    daily = group.find("control[@id='310']")
    breaking = group.find("control[@id='311']")
    refresh = group.find("control[@id='301']")
    button = copy.deepcopy(breaking)
    button.set('id','312')
    for key,value in dict(left='1004',width='220',label='Read briefing',onleft='311',
            onright='301',onup='312',onclick='RunScript(/storage/.aster-staging/'+READER+
            '/default.py,'+READER_PIN+',news)').items(): button.find(key).text=value
    breaking.find('onright').text='312'
    refresh.find('left').text='1236'
    refresh.find('onleft').text='312'
    group.insert(list(group).index(refresh),button)
    backing = group.find("control[@type='image']")
    if backing.findtext('left')!='542' or backing.findtext('width')!='620':
        raise ValueError('exact-read-news-rail-required')
    backing.find('width').text='852'
    rings = [node for node in group.findall("control[@type='image']")
             if node.findtext('visible')=='Control.HasFocus(301)']
    if len(rings)!=1: raise ValueError('exact-read-news-focus-ring-required')
    rings[0].find('left').text='1235'
    ring = copy.deepcopy(rings[0])
    ring.find('left').text='1003';ring.find('width').text='222'
    ring.find('visible').text='Control.HasFocus(312)'
    group.append(ring)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'


def build(output, source):
    here = Path(__file__).resolve().parent
    output = Path(output)
    if output.exists(): raise ValueError('immutable-read-news-output')
    raw = patch_page(Path(source).read_bytes())
    path = output/'payload'/TARGET
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw)
    helpers = {}
    for name in ('digest_read_news_install.py','deploy_digest_read_news.py','digest_news_install.py'):
        data = (here/name if name!='deploy_digest_read_news.py' else here/'tools'/name).read_bytes()
        (output/name).write_bytes(data)
        helpers[name] = hashlib.sha256(data).hexdigest()
    manifest = dict(kind='hp-digest-read-news.v1',reader_manifest_sha256=READER_PIN,
        files=[dict(path=TARGET,before_sha256=BEFORE,sha256=hashlib.sha256(raw).hexdigest())],helpers=helpers)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return hashlib.sha256((output/'manifest.json').read_bytes()).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True);parser.add_argument('--source',required=True)
    args=parser.parse_args();print(build(args.output,args.source))
