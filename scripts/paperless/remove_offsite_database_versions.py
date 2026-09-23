"""One-time exact Paperless archive cleanup on relay 112; dry-run by default.

Credentials remain source-local. Never deletes another key, a local archive,
service exports, or a whole bucket/prefix. Run only under explicit approval.
"""
import configparser
import json
import os
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, '/opt/paperless-cleanup-lib')
import boto3
from botocore.config import Config

NAMES = [
 'vzdump-lxc-115-2026_09_16-02_44_21.tar.zst',
 'vzdump-lxc-115-2026_09_17-02_44_31.tar.zst',
 'vzdump-lxc-115-2026_09_18-02_44_19.tar.zst',
 'vzdump-lxc-115-2026_09_19-02_44_38.tar.zst',
 'vzdump-lxc-115-2026_09_20-02_44_38.tar.zst',
 'vzdump-lxc-115-2026_09_21-02_44_54.tar.zst',
 'vzdump-lxc-115-2026_09_22-02_44_43.tar.zst',
]
c = configparser.ConfigParser(interpolation=None)
c.read('/etc/rclone/rclone.conf')
remote, target = c['idrive-crypt']['remote'].split(':', 1)
bucket, _, prefix = target.partition('/')
assert bucket == 'homelab-backup-relay'
s = c[remote]
client = boto3.client('s3', endpoint_url=s['endpoint'] if s['endpoint'].startswith('https://') else 'https://' + s['endpoint'],
 aws_access_key_id=s['access_key_id'], aws_secret_access_key=s['secret_access_key'],
 region_name=s.get('region') or 'us-east-1', config=Config(retries={'max_attempts': 3},connect_timeout=15,read_timeout=30))
assert Path('/srv/backup/homelab-proxmox-guests/'+NAMES[5]).stat().st_size == 2192949035
assert "--exclude '/homelab-proxmox-guests/vzdump-lxc-115-*.tar.zst'" in Path('/usr/local/sbin/idrive-relay-sync').read_text()
entries = []
for name in NAMES:
 encoded = subprocess.check_output(['/usr/local/bin/rclone','--config','/etc/rclone/rclone.conf','backend','encode','idrive-crypt:','homelab-proxmox-guests/'+name],text=True).strip()
 key = '/'.join(p for p in (prefix.rstrip('/'), encoded) if p)
 for page in client.get_paginator('list_object_versions').paginate(Bucket=bucket,Prefix=key):
  for row in page.get('Versions',[]) + page.get('DeleteMarkers',[]):
   if row['Key'] == key:
    entries.append({'name':name,'Key':key,'VersionId':row['VersionId']})
print(json.dumps({'exact_archive_names':NAMES,'version_count':len(entries),'mode':'apply' if '--apply' in sys.argv else 'dry-run'}))
if '--apply' in sys.argv:
 checkpoint=Path('/root/paperless-offsite-version-removal-20260923.json')
 with os.fdopen(os.open(checkpoint,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:json.dump(entries,f)
 for row in entries:
  client.delete_object(Bucket=bucket,Key=row['Key'],VersionId=row['VersionId'])
 for key in {row['Key'] for row in entries}:
  for page in client.get_paginator('list_object_versions').paginate(Bucket=bucket,Prefix=key):
   assert not any(row['Key']==key for row in page.get('Versions',[])+page.get('DeleteMarkers',[])), 'Versions remain'
 print(json.dumps({'removed_versions':len(entries),'verified_remaining_versions':0,'local_archives_unchanged':True}))
