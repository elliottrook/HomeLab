#!/usr/bin/env python3
"""Protected, media-free TrueNAS configuration export. Run as root on TrueNAS.

SQLite uses online backup + integrity checks. File Browser's Bolt DB is copied
while its container is briefly paused. No contents or credentials are logged.
Archive restores are hash checked before atomic publication. Previous exports
are preserved by the backup-hub snapshot/crypt versioning policies.
"""
from contextlib import closing
import sys,signal
import datetime,fcntl,hashlib,json,os,pathlib,shutil,sqlite3,subprocess,tarfile,tempfile,time,urllib.request
P=pathlib.Path
ROOT=P('/mnt/Recovery/configuration/exports/truenas')
SKIP={'metadata','cache','.cache','logs','log','log_archive','transcodes','thumbnails','MediaCover','Sentry','Backups','backups','SQLiteBackups','Downloads','processed_books','.cwa_conversion_tmp','streams','tmp','listsCache','gravity_backups','config_backups','migration_backup','perm-fix-backup'}
MEDIA={'.mp4','.mkv','.avi','.mov','.m4v','.mp3','.m4b','.m4a','.flac','.aac','.ogg','.wav','.epub','.pdf','.mobi','.azw3','.cbz','.cbr','.iso'}
MOUNTS={
'newtarr':{'/appdata'},'prowlarr':{'/config','/appdata'},'lidarr':{'/config','/appdata'},
'sonarr':{'/config','/appdata'},'radarr':{'/config','/appdata'},'sabnzbd':{'/config','/appdata'},
'bazarr':{'/config'},
'jellyfin':{'/config'},'ix-pihole-pihole-1':{'/etc/pihole','/etc/dnsmasq.d'},
'ix-filebrowser-filebrowser-1':{'/config','/database'},'dozzle':{'/data'},
'ix-dockge-dockge-1':{'/app/data'},'flaresolverr':{'/config'},
'calibre':{'/config'},'calibre-web-automated':{'/config'},'seerr':{'/app/config'},'profilarr':{'/config'},
'ix-audiobookshelf-audiobookshelf-1':{'/config','/metadata'},
'unified-lazylibrarian-shadow':{'/config'},
'unified-audiobookshelf-shadow':{'/config'}}

def run(*args):return subprocess.check_output(args,stderr=subprocess.PIPE)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def copy_config(src,dst,dbs,excludes=()):
 src=P(src)
 if src.is_symlink():
  dst.parent.mkdir(parents=True,exist_ok=True);dst.symlink_to(os.readlink(src));return
 if src.is_dir():
  dst.mkdir(parents=True,exist_ok=True)
  for p in src.iterdir():
   if p.name in SKIP or p.name in excludes or '.before-' in p.name or '-before-' in p.name:continue
   copy_config(p,dst/p.name,dbs)
  return
 if not src.is_file():return
 if src.suffix.lower() in MEDIA or src.name.endswith(('-wal','-shm','.pid','.log')) or src.name in {'logs.db','pihole-FTL.db','gravity_old.db'}:return
 dst.parent.mkdir(parents=True,exist_ok=True)
 with src.open('rb') as f:isdb=f.read(16)==b'SQLite format 3\0'
 if isdb:
  start=time.monotonic()
  def progress(status,remaining,total):
   if time.monotonic()-start>120:raise TimeoutError('SQLite backup exceeded deadline')
  with closing(sqlite3.connect(src.as_uri()+'?mode=ro',uri=True,timeout=10)) as a,closing(sqlite3.connect(dst)) as b:
   a.backup(b,pages=256,progress=progress,sleep=.05)
   b.commit();b.execute('PRAGMA wal_checkpoint(TRUNCATE)');b.execute('PRAGMA journal_mode=DELETE')
   assert b.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  for suffix in ('-wal','-shm'):
   P(str(dst)+suffix).unlink(missing_ok=True)
  dbs.append(str(dst))
 else:
  for attempt in range(3):
   before=src.stat();shutil.copy2(src,dst);after=src.stat()
   if (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns):break
  else:raise RuntimeError('Configuration changed repeatedly during copy')
 dst.chmod(0o600)

def backup_abs(dst, name='ix-audiobookshelf-audiobookshelf-1'):
 dst.parent.mkdir(parents=True,exist_ok=True)
 tmp='/tmp/homelab-config-'+str(os.getpid())+'.sqlite'
 code=r"""process.umask(0o077); const s=require('sqlite3');const p=process.argv[1];
 const db=new s.Database('/config/absdatabase.sqlite',s.OPEN_READONLY);
 db.configure('busyTimeout',30000);
 db.exec('VACUUM INTO '+JSON.stringify(p),e=>{if(e)throw e;db.close();
 const b=new s.Database(p,s.OPEN_READONLY);b.get('PRAGMA integrity_check',(e,r)=>{
 if(e||Object.values(r)[0]!=='ok')throw e||Error('integrity');b.close();});});"""
 try:
  run('docker','exec','--user','0',name,'node','-e',code,tmp)
  run('docker','cp',name+':'+tmp,str(dst));dst.chmod(0o600)
 finally:
  run('docker','exec','--user','0',name,'node','-e',"require('fs').rmSync(process.argv[1],{force:true})",tmp)

def main():
 signal.signal(signal.SIGTERM,lambda signum,frame:sys.exit(143))
 os.umask(0o077);ROOT.mkdir(parents=True,exist_ok=True);ROOT.chmod(0o700)
 lock=open(ROOT/'export.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 work=P(tempfile.mkdtemp(prefix='.candidate-',dir=ROOT));payload=work/'payload';payload.mkdir();dbs=[]
 try:
  allc=json.loads(run('docker','inspect',*run('docker','ps','-aq').decode().split()))
  containers={c['Name'].lstrip('/'):c for c in allc}
  assert set(MOUNTS)<=set(containers),'Expected application missing; review inventory'
  unknown=[n for n,c in containers.items() if c['State']['Running'] and n not in MOUNTS and any(m['Destination'] in {'/config','/app/config','/appdata','/database'} for m in c['Mounts'])]
  assert not unknown,'Unclassified application config mount; update backup scope'
  covered=[]
  for name,targets in MOUNTS.items():
   c=containers[name];selected=[m for m in c['Mounts'] if m['Destination'] in targets]
   assert {m['Destination'] for m in selected}==targets,'Config mount changed; review inventory'
   dest=payload/'apps'/name;dest.mkdir(parents=True)
   (dest/'container.json').write_text(json.dumps(c))
   paused=False
   try:
    if name=='ix-filebrowser-filebrowser-1' and c['State']['Running']:
     assert not c['State']['Paused'];run('docker','pause',name);paused=True
    for m in selected:
     source=P(m['Source'])
     allowed=[P('/mnt/Media/appdata'),P('/mnt/.ix-apps/app_mounts'),P('/mnt/.ix-apps/docker/volumes'),P('/mnt/Media/apps/calibre-web-automated/config')]
     exact={P('/mnt/Media/media/audiobooks'),P('/mnt/Media/configs')}
     assert source in exact or any(source==root or root in source.parents for root in allowed),'Unexpected configuration source; review scope'
     target=dest/'mounts'/m['Destination'].strip('/').replace('/','_')
     if name=='calibre':
      for child in ['.bashrc','.config','.local','.pki','.dbus','.XDG','ssl']:
       if (source/child).exists():copy_config(source/child,target/child,dbs)
      catalogue=source/'Calibre Library/metadata.db'
      if catalogue.exists():copy_config(catalogue,target/'Calibre Library/metadata.db',dbs)
     elif name in {'ix-audiobookshelf-audiobookshelf-1','unified-audiobookshelf-shadow'} and m['Destination']=='/config':
      assert (source/'absdatabase.sqlite').is_file()
      backup_abs(target/'absdatabase.sqlite', name);dbs.append(str(target/'absdatabase.sqlite'))
      if (source/'migrations').is_dir():copy_config(source/'migrations',target/'migrations',dbs)
     else:copy_config(source,target,dbs,{'metadata','subtitles'} if name=='jellyfin' and source.name=='data' else ())
   finally:
    if paused:run('docker','unpause',name)
   covered.append(name)
  catalogue=P('/mnt/Media/media/books/metadata.db')
  assert catalogue.is_file(),'Calibre catalogue missing; review library mapping'
  copy_config(catalogue,payload/'calibre-library-catalogue/metadata.db',dbs)
  # The large Jellyfin artwork tree is disposable; library/collection XML is retained.
  # Guard definitions, managed app settings and exact network reconstruction are config.
  for source,label in [('/mnt/Media/appdata/authentik-browser-ingress','browser-guards'),('/mnt/.ix-apps/app_configs','managed-apps'),('/mnt/Media/data/tools','automation-tools'),('/root/.ssh','host-ssh'),('/etc/ssh','ssh-service'),('/mnt/Media/appdata/config-backup-tools','backup-tools')]:
   copy_config(source,payload/label,dbs)
  (payload/'docker-networks.json').write_bytes(run('docker','network','inspect',*run('docker','network','ls','-q').decode().split()))
  (payload/'containers-inventory.json').write_text(json.dumps(allc))
  # Native export includes the seed needed to decrypt stored application credentials.
  from truenas_api_client import Client
  with Client() as client:
   job,url=client.call('core.download','config.save',[{'secretseed':True,'root_authorized_keys':True}],'truenas-config.tar')
   with urllib.request.urlopen('http://127.0.0.1'+url,timeout=90) as r:(payload/'truenas-config.tar').write_bytes(r.read())
  with tarfile.open(payload/'truenas-config.tar') as tf:
   members=tf.getmembers();assert any(m.name.endswith('.db') for m in members),'Missing TrueNAS database'
   for m in members:
    if m.isfile() and m.name.endswith('.db'):
     check=work/'truenas-check.db';check.write_bytes(tf.extractfile(m).read())
     with sqlite3.connect(check) as con:assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  hashes={str(p.relative_to(payload)):digest(p) for p in payload.rglob('*') if p.is_file() and not p.is_symlink()}
  assert len(dbs)>=18,'Expected database inventory changed; review before publication'
  manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'apps':covered,'files':hashes,'sqlite_databases':len(dbs),'media_included':False,'scope':'configuration and restoration-critical account state; excludes media, caches, DNS query history'}
  (payload/'manifest.json').write_text(json.dumps(manifest,indent=2))
  archive=work/'configs.tar.gz'
  with tarfile.open(archive,'w:gz',compresslevel=3) as t:t.add(payload,arcname='configuration')
  with tarfile.open(archive,'r:gz') as t:
   for member in t:
    assert not member.name.startswith('/') and '..' not in P(member.name).parts
    if member.isfile() and member.name!='configuration/manifest.json':
     h=hashlib.sha256();f=t.extractfile(member)
     for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
     assert h.hexdigest()==hashes[member.name.removeprefix('configuration/')]
  result={'created_utc':manifest['created_utc'],'apps':covered,'files_verified':len(hashes),'sqlite_verified':len(dbs),'archive_sha256':digest(archive),'archive_bytes':archive.stat().st_size,'media_included':False}
  # Two generations survive an interrupted publication; existing snapshot retention adds history.
  current=ROOT/'configs.tar.gz';previous=ROOT/'configs.previous.tar.gz'
  if current.exists():
   prior=ROOT/'.previous-candidate';prior.unlink(missing_ok=True);os.link(current,prior);os.replace(prior,previous)
  os.replace(archive,current);current.chmod(0o600)
  status=ROOT/'status.candidate.json';status.write_text(json.dumps(result,indent=2));os.replace(status,ROOT/'status.json')
  (ROOT/'failure.json').unlink(missing_ok=True)
  print(json.dumps(result))
 finally:
  shutil.rmtree(work)
if __name__=='__main__':
 try:main()
 except BlockingIOError:
  print('Configuration backup already running; skipped')
 except BaseException as error:
  if ROOT.is_dir():
   (ROOT/'failure.json').write_text(json.dumps({'failed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error_class':type(error).__name__}))
  print('Configuration backup failed: '+type(error).__name__,file=sys.stderr)
  sys.exit(1)
