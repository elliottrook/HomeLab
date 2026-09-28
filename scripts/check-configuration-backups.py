#!/usr/bin/env python3
"""Read-only freshness/manifest checks; never print configuration contents."""
import datetime,json,subprocess,sys
REMOTE=r'''import json,pathlib,datetime
r=pathlib.Path('/mnt/Media/backup/configuration/truenas');s=json.loads((r/'status.json').read_text());p=r/'configs.tar.gz'
print(json.dumps({'created_utc':s['created_utc'],'apps':len(s['apps']),'sqlite_verified':s['sqlite_verified'],'media_included':s['media_included'],'size_matches':p.stat().st_size==s['archive_bytes'],'failure':(r/'failure.json').exists()}))'''
def assess(s,now):
 age=(now-datetime.datetime.fromisoformat(s['created_utc'])).total_seconds()/3600
 return age>=0 and age<30 and s['apps']>=17 and s['sqlite_verified']>=18 and s['size_matches'] and not s['media_included'] and not s['failure'],age

def synology_status(now):
 code="""import json,pathlib
r=pathlib.Path('/mnt/Media/backup/gowest/homes/.homelab-config-backups');s=json.loads((r/'status.json').read_text());print(json.dumps({'created_utc':s['created_utc'],'size_matches':(r/'configs.tar.gz').stat().st_size==s['archive_bytes'],'photos_included':s['photos_included'],'databases':len(s['databases']),'failure':(r/'failure.json').exists()}))"""
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','truenas','sudo -n python3 -'],input=code,text=True,capture_output=True,timeout=20)
 if r.returncode:return False,'Synology config copy unavailable'
 s=json.loads(r.stdout);age=(now-datetime.datetime.fromisoformat(s['created_utc'])).total_seconds()/3600
 timer=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','gowest','systemctl is-active homelab-config-backup.timer'],capture_output=True,text=True,timeout=20)
 ok=0<=age<30 and s['size_matches'] and not s['photos_included'] and not s['failure'] and s['databases']>=2 and timer.stdout.strip()=='active'
 return ok,f"Synology config copy — age {age:.1f}h, photos excluded={not s['photos_included']}, timer active={timer.stdout.strip()=='active'}"

def main():
 r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','truenas','sudo -n python3 -'],input=REMOTE,text=True,capture_output=True,timeout=20)
 if r.returncode:print('FAIL: TrueNAS configuration backup status unavailable');return 1
 try:
  s=json.loads(r.stdout);ok,age=assess(s,datetime.datetime.now(datetime.timezone.utc))
 except (KeyError,ValueError,TypeError):print('FAIL: invalid configuration backup status');return 1
 print(('PASS' if ok else 'FAIL')+f": TrueNAS configs — {s['apps']} apps, {s['sqlite_verified']} databases, age {age:.1f}h, media excluded={not s['media_included']}")
 try:syn_ok,message=synology_status(datetime.datetime.now(datetime.timezone.utc))
 except (KeyError,ValueError,TypeError,subprocess.TimeoutExpired):syn_ok,message=False,'Synology config status unavailable'
 print(('PASS: ' if syn_ok else 'FAIL: ')+message)
 return 0 if ok and syn_ok else 1
if __name__=='__main__':sys.exit(main())
