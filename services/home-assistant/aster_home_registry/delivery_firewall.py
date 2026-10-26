"""One host/port-only HA-to-HP rule; no alias, WAN or unrelated rule edits."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid
import xml.etree.ElementTree as ET

RULE_ID=str(uuid.uuid5(uuid.NAMESPACE_URL,'aster-home-delivery-ha-hp-v1'))
REFERENCE='da196b4e-8147-4afa-b7f0-24f0d628ee15'
VALUES=dict(enabled='1',sequence='1850',action='pass',interface='opt3',direction='in',
            ipprotocol='inet',protocol='TCP',source_net='192.168.20.11',source_not='0',
            destination_net='192.168.1.140',destination_not='0',destination_port='22',
            description='Aster Home HA to HP restricted display feed')

def change(root,mode):
    rules=list(root.iter('rule'));owned=[n for n in rules if n.get('uuid')==RULE_ID]
    if len(owned)>1:raise ValueError('feed-rule-duplicate')
    if owned:
        if any(owned[0].findtext(k)!=v for k,v in VALUES.items()):raise ValueError('feed-rule-drift')
        if mode=='rollback':
            next(p for p in root.iter() if owned[0] in list(p)).remove(owned[0]);return True
        return False
    if mode in ('verify','rollback'):
        if mode=='verify':raise ValueError('feed-rule-missing')
        return False
    if any(n.findtext('sequence')=='1850' for n in rules):raise ValueError('feed-rule-sequence-used')
    reference=next(n for n in rules if n.get('uuid')==REFERENCE)
    if reference.findtext('interface')!='opt3' or reference.findtext('source_net')!='192.168.20.11':raise ValueError('feed-rule-reference-drift')
    candidate=copy.deepcopy(reference);candidate.set('uuid',RULE_ID)
    for key,value in VALUES.items():
        node=candidate.find(key)
        if node is None:node=ET.SubElement(candidate,key)
        node.text=value
    parent=next(p for p in root.iter() if reference in list(p));parent.append(candidate)
    return True

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('preview','apply','verify','rollback'));args=parser.parse_args()
    path=Path('/conf/config.xml');before=path.read_bytes();root=ET.fromstring(before)
    changed=change(root,args.mode)
    result=dict(rule_id=RULE_ID,mode=args.mode,changed=changed,source='192.168.20.11',destination='192.168.1.140',tcp_port=22)
    if changed and args.mode in ('apply','rollback'):
        cp=Path('/conf/backup')/('config-aster-home-feed-'+args.mode+'-20261026.xml')
        fd=os.open(str(cp),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(before);stream.flush();os.fsync(stream.fileno())
        if cp.read_bytes()!=before:raise ValueError('feed-rule-backup')
        with tempfile.TemporaryDirectory(prefix='aster-rule-restore-',dir='/root') as folder:
            restored=Path(folder)/'config.xml';restored.write_bytes(cp.read_bytes())
            if hashlib.sha256(restored.read_bytes()).digest()!=hashlib.sha256(before).digest():raise ValueError('feed-rule-restore')
            ET.parse(restored)
        # Prove that removing only the candidate recovers the parsed original.
        check=copy.deepcopy(root)
        if args.mode=='apply':change(check,'rollback')
        else:change(check,'apply')
        original=ET.fromstring(before)
        def rules_free(node):
            n=copy.deepcopy(node)
            for p in n.iter():
                for c in list(p):
                    if c.tag=='rule' and c.get('uuid')==RULE_ID:p.remove(c)
            return ET.tostring(n)
        if rules_free(root)!=rules_free(original):raise ValueError('feed-rule-other-config')
        metadata=path.stat();fd,tmp=tempfile.mkstemp(prefix='.aster-home-feed.',dir=path.parent)
        with os.fdopen(fd,'wb') as stream:stream.write(ET.tostring(root,encoding='utf-8'));stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,metadata.st_mode&0o777);os.chown(tmp,metadata.st_uid,metadata.st_gid)
        if path.read_bytes()!=before:raise ValueError('feed-rule-concurrent-change')
        os.replace(tmp,path)
        result.update(checkpoint=str(cp),isolated_restore=True,reload_required=True)
    print(json.dumps(result))

if __name__=='__main__':main()
