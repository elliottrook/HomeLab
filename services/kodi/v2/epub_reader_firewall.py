"""One HP-to-TrueNAS NFSv4 rule; source-local OPNsense mutation."""
import argparse,copy,hashlib,json,os,tempfile,uuid
from pathlib import Path
import xml.etree.ElementTree as ET

RULE_ID=str(uuid.uuid5(uuid.NAMESPACE_URL,'aster-books-hp-truenas-nfsv4-v1'))
REFERENCE='d8c1a44e-e726-4442-99e2-2093f209799e'
VALUES=dict(enabled='1',sequence='3095',action='pass',interface='lan',direction='in',
 ipprotocol='inet',protocol='TCP',source_net='192.168.1.140',source_not='0',
 destination_net='192.168.20.40',destination_not='0',destination_port='2049',
 description='AsterTV HP read-only published EPUB narration NFSv4')

def change(root,mode):
 rules=list(root.iter('rule'));owned=[n for n in rules if n.get('uuid')==RULE_ID]
 if len(owned)>1:raise ValueError('epub-rule-duplicate')
 if owned:
  if any(owned[0].findtext(k)!=v for k,v in VALUES.items()):raise ValueError('epub-rule-drift')
  if mode=='rollback':next(p for p in root.iter() if owned[0] in list(p)).remove(owned[0]);return True
  return False
 if mode in ('verify','rollback'):
  if mode=='verify':raise ValueError('epub-rule-missing')
  return False
 if any(n.findtext('sequence')==VALUES['sequence'] for n in rules):raise ValueError('epub-rule-sequence-used')
 ref=next(n for n in rules if n.get('uuid')==REFERENCE)
 if ref.findtext('interface')!='lan' or ref.findtext('source_net')!='192.168.1.140':raise ValueError('epub-rule-reference-drift')
 candidate=copy.deepcopy(ref);candidate.set('uuid',RULE_ID)
 for key,value in VALUES.items():
  node=candidate.find(key)
  if node is None:node=ET.SubElement(candidate,key)
  node.text=value
 next(p for p in root.iter() if ref in list(p)).append(candidate);return True

def main():
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('preview','apply','verify','rollback'));args=parser.parse_args()
 path=Path('/conf/config.xml');before=path.read_bytes();root=ET.fromstring(before);changed=change(root,args.mode)
 result=dict(rule_id=RULE_ID,mode=args.mode,changed=changed,source='192.168.1.140',destination='192.168.20.40',tcp_port=2049)
 if changed and args.mode in ('apply','rollback'):
  cp=Path('/conf/backup')/('config-aster-epub-nfs-'+args.mode+'-20261026.xml')
  fd=os.open(str(cp),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb') as stream:stream.write(before);stream.flush();os.fsync(stream.fileno())
  if cp.read_bytes()!=before:raise ValueError('epub-rule-backup')
  with tempfile.TemporaryDirectory(prefix='aster-epub-rule-',dir='/root') as folder:
   restored=Path(folder)/'config.xml';restored.write_bytes(cp.read_bytes());ET.parse(restored)
   if hashlib.sha256(restored.read_bytes()).digest()!=hashlib.sha256(before).digest():raise ValueError('epub-rule-restore')
  metadata=path.stat();fd,tmp=tempfile.mkstemp(prefix='.aster-epub-nfs.',dir=path.parent)
  with os.fdopen(fd,'wb') as stream:stream.write(ET.tostring(root,encoding='utf-8'));stream.flush();os.fsync(stream.fileno())
  os.chmod(tmp,metadata.st_mode&0o777);os.chown(tmp,metadata.st_uid,metadata.st_gid)
  if path.read_bytes()!=before:raise ValueError('epub-rule-concurrent-change')
  os.replace(tmp,path);result.update(checkpoint=str(cp),isolated_restore=True,reload_required=True)
 print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
