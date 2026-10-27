"""Create or remove only HP's two read-only TrueNAS publication exports."""
import argparse,json,subprocess
from pathlib import Path

ROOT='/mnt/Media/AsterReader';HOST='192.168.1.140'
PATHS=(ROOT+'/ready',ROOT+'/generations')
CP=Path('/root/.aster-checkpoints/aster-epub-reader-consumer-20261026')
def call(method,*args):
 p=subprocess.run(['midclt','call',method,*[json.dumps(x,separators=(',',':')) for x in args]],capture_output=True,text=True,check=True)
 return json.loads(p.stdout)
def wanted(path):return dict(path=path,hosts=[HOST],networks=[],ro=True,maproot_user='root',maproot_group=None,mapall_user=None,mapall_group=None,security=['SYS'],enabled=True,expose_snapshots=False,comment='AsterTV HP read-only published EPUB narration')
def legacy(path):
 row=wanted(path);row['maproot_user']=None;return row
def owned(rows):return {r['path']:r for r in rows if r.get('path') in PATHS}
def verify_row(row,path):
 expected=wanted(path)
 for key,value in expected.items():
  if row.get(key)!=value:raise ValueError('epub-export-drift-'+key)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('preview','apply','repair','verify','rollback'));args=parser.parse_args()
 rows=call('sharing.nfs.query');current=owned(rows)
 if args.mode=='preview':
  if current:raise ValueError('epub-export-already-present')
  print(json.dumps(dict(mode='preview',paths=PATHS,host=HOST,read_only=True),sort_keys=True));return
 if args.mode=='apply':
  if current or CP.exists():raise ValueError('epub-export-predecessor-drift')
  CP.mkdir(mode=0o700,parents=True);(CP/'state.json').write_text(json.dumps(dict(schema=1,paths=PATHS,absent=True),sort_keys=True)+'\n');(CP/'state.json').chmod(0o600)
  created=[]
  try:
   for path in PATHS:created.append(call('sharing.nfs.create',wanted(path)))
  except Exception:
   for row in reversed(created):call('sharing.nfs.delete',row['id'])
   raise
  current=owned(call('sharing.nfs.query'))
  if set(current)!=set(PATHS):raise ValueError('epub-export-create-incomplete')
  for path,row in current.items():verify_row(row,path)
 elif args.mode=='repair':
  if not CP.is_dir() or json.loads((CP/'state.json').read_text())!=dict(schema=1,paths=list(PATHS),absent=True):raise ValueError('epub-export-checkpoint')
  if set(current)!=set(PATHS):raise ValueError('epub-export-repair-missing')
  for path,row in current.items():
   expected=legacy(path)
   for key,value in expected.items():
    if row.get(key)!=value:raise ValueError('epub-export-repair-drift-'+key)
  for path,row in current.items():call('sharing.nfs.update',row['id'],wanted(path))
  current=owned(call('sharing.nfs.query'))
  for path,row in current.items():verify_row(row,path)
 elif args.mode=='verify':
  if not CP.is_dir() or json.loads((CP/'state.json').read_text())!=dict(schema=1,paths=list(PATHS),absent=True):raise ValueError('epub-export-checkpoint')
  if set(current)!=set(PATHS):raise ValueError('epub-export-missing')
  for path,row in current.items():verify_row(row,path)
 else:
  if not CP.is_dir():raise ValueError('epub-export-checkpoint')
  for path,row in current.items():verify_row(row,path)
  for row in current.values():call('sharing.nfs.delete',row['id'])
  if owned(call('sharing.nfs.query')):raise ValueError('epub-export-rollback')
 print(json.dumps(dict(mode=args.mode,paths=PATHS,host=HOST,read_only=True,passed=True),sort_keys=True))
if __name__=='__main__':main()
