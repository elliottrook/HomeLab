#!/usr/bin/env python3
"""Root-only DSM/Immich configuration backup; excludes library and model cache."""
import datetime,fcntl,gzip,hashlib,json,os,pathlib,shutil,subprocess,tarfile,tempfile
P=pathlib.Path
ROOT=P('/volume1/homes/.homelab-config-backups')
DOCKER='/usr/local/bin/docker'
def run(args,**kw):return subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,**kw)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 os.umask(0o077);ROOT.mkdir(mode=0o700,exist_ok=True);ROOT.chmod(0o700)
 lock=open(str(ROOT/'backup.lock'),'w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 work=P(tempfile.mkdtemp(prefix='homelab-config-',dir='/volume1/docker'));payload=work/'configuration';payload.mkdir()
 try:
  conf=payload/'synology.dss'
  run(['/usr/syno/bin/synoconfbkp','export','--filepath='+str(conf)])
  assert conf.is_file() and conf.stat().st_size>1024,'DSM configuration export missing'
  ids=run([DOCKER,'ps','-aq']).stdout.decode().split();inventory=json.loads(run([DOCKER,'inspect']+ids).stdout)
  (payload/'containers.json').write_text(json.dumps(inventory))
  app=P('/volume1/docker/dockge/stacks/immich-app');dst=payload/'immich-deployment';dst.mkdir()
  for p in app.iterdir():
   if p.is_file() and (p.name.startswith('.env') or p.suffix in {'.yaml','.yml','.json','.sh','.conf'}):shutil.copy2(str(p),str(dst/p.name))
  assert (dst/'compose.yaml').exists() or any(dst.glob('*.yml')) or (dst/'docker-compose.yaml').exists(),'Compose definition missing'
  # Dump every non-template app database, including roles; no media payload is read.
  names=run([DOCKER,'exec','immich_postgres','sh','-c','exec psql -U "${POSTGRES_USER:-postgres}" -d postgres -Atc "SELECT datname FROM pg_database WHERE NOT datistemplate"']).stdout.decode().splitlines()
  runargs=[DOCKER,'exec','immich_postgres','sh','-c','exec pg_dumpall --roles-only -U "${POSTGRES_USER:-postgres}"']
  (payload/'postgres-roles.sql').write_bytes(run(runargs).stdout)
  dumps=[]
  for index,name in enumerate(names):
   out=payload/('database-'+str(index)+'.dump')
   with out.open('wb') as f:subprocess.run([DOCKER,'exec','immich_postgres','sh','-c','exec pg_dump -Fc -U "${POSTGRES_USER:-postgres}" --dbname="$1"','backup',name],stdout=f,stderr=subprocess.PIPE,check=True)
   with out.open('rb') as f:r=subprocess.run([DOCKER,'exec','-i','immich_postgres','pg_restore','--list'],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
   assert len(r.stdout)>100
   dumps.append({'database':name,'file':out.name,'catalogue_verified':True})
  # Supplemental host/package configuration; vendor DSS remains the primary DSM restore path.
  with tarfile.open(str(payload/'host-config.tar.gz'),'w:gz') as t:
   for source in ['/etc','/usr/syno/etc','/root/.ssh','/usr/local/sbin/homelab-synology-configs.py','/etc/systemd/system/homelab-config-backup.service','/etc/systemd/system/homelab-config-backup.timer']:
    if P(source).exists():t.add(source,arcname=source.lstrip('/'),recursive=True)
  hashes={str(p.relative_to(payload)):sha(p) for p in payload.rglob('*') if p.is_file()}
  manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':hashes,'databases':dumps,'photos_included':False,'model_cache_included':False}
  (payload/'manifest.json').write_text(json.dumps(manifest,indent=2))
  archive=work/'configs.tar.gz'
  with tarfile.open(str(archive),'w:gz') as t:t.add(str(payload),arcname='configuration')
  with tarfile.open(str(archive)) as t:
   for m in t:
    if m.isfile() and m.name!='configuration/manifest.json':
     assert hashlib.sha256(t.extractfile(m).read()).hexdigest()==hashes[m.name[len('configuration/'):]]
  candidate=ROOT/'configs.candidate.tar.gz';shutil.copyfile(str(archive),str(candidate))
  current=ROOT/'configs.tar.gz'
  if current.exists():os.replace(str(current),str(ROOT/'configs.previous.tar.gz'))
  os.replace(str(candidate),str(current))
  status={'created_utc':manifest['created_utc'],'archive_sha256':sha(current),'archive_bytes':current.stat().st_size,'files_verified':len(hashes),'databases':dumps,'photos_included':False}
  p=ROOT/'status.candidate.json';p.write_text(json.dumps(status,indent=2));os.replace(str(p),str(ROOT/'status.json'))
  public=P('/tmp/homelab-synology-config-status.json');public.write_text(json.dumps(status));public.chmod(0o644)
  failure=ROOT/'failure.json'
  if failure.exists():failure.unlink()
  print('Synology configuration backup verified; Immich photos excluded. Daily timer may now be enabled.')
 except Exception as e:
  failure={'failed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error_class':type(e).__name__}
  (ROOT/'failure.json').write_text(json.dumps(failure))
  print('Backup failed: '+type(e).__name__+'; no success claimed.')
  raise
 finally:shutil.rmtree(str(work))
if __name__=='__main__':main()
