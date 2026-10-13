#!/usr/bin/env python3
"""Bounded 2026-10-07 cleanup and ongoing read-only cloud usage audit.

Run on relay LXC 112. Credentials stay in the existing root-only rclone config.
Only --execute-20261007 permits writes, for the exact reviewed guest versions.
"""
import argparse
import base64
import collections
import configparser
import datetime
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BUCKET = 'homelab-backup-relay'
STATE = Path('/var/lib/idrive-version-maintenance')
CONFIG = '/etc/rclone/rclone.conf'
EXPECTED_COUNT = 405
EXPECTED_BYTES = 1021053826174

def tag(e): return e.tag.rsplit('}', 1)[-1]
def fields(e): return {tag(x): x.text for x in e}

class S3:
    def __init__(self):
        c = configparser.ConfigParser(interpolation=None)
        c.read(CONFIG)
        self.c = c['idrive-e2']
        assert c['idrive-crypt']['remote'] == 'idrive-e2:' + BUCKET
        self.host = urllib.parse.urlsplit('https://' + self.c['endpoint'].removeprefix('https://')).netloc

    def request(self, method, params, body=b''):
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        day, region = stamp[:8], self.c.get('region') or 'us-east-1'
        query = urllib.parse.urlencode(sorted(params.items()), quote_via=urllib.parse.quote)
        path = '/' + BUCKET
        hashed = hashlib.sha256(body).hexdigest()
        headers = {'host': self.host, 'x-amz-content-sha256': hashed, 'x-amz-date': stamp}
        if body:
            headers['content-md5'] = base64.b64encode(hashlib.md5(body).digest()).decode()
        signed = ';'.join(sorted(headers))
        canonical = '\n'.join([method, path, query, ''.join(k+':'+headers[k]+'\n' for k in sorted(headers)), signed, hashed])
        scope = day+'/'+region+'/s3/aws4_request'
        string = 'AWS4-HMAC-SHA256\n'+stamp+'\n'+scope+'\n'+hashlib.sha256(canonical.encode()).hexdigest()
        key = ('AWS4'+self.c['secret_access_key']).encode()
        for value in [day, region, 's3', 'aws4_request']:
            key = hmac.new(key, value.encode(), hashlib.sha256).digest()
        signature = hmac.new(key, string.encode(), hashlib.sha256).hexdigest()
        headers['Authorization'] = 'AWS4-HMAC-SHA256 Credential='+self.c['access_key_id']+'/'+scope+', SignedHeaders='+signed+', Signature='+signature
        req = urllib.request.Request('https://'+self.host+path+'?'+query, data=body if body else None, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read()
        except urllib.error.HTTPError as error:
            root = ET.fromstring(error.read())
            raise RuntimeError('S3 '+str(error.code)+' '+str(fields(root).get('Code'))) from None
        return ET.fromstring(data) if data else ET.Element('Empty')

    def versions(self, prefix=''):
        params = {'versions': '', 'max-keys': '1000', 'prefix': prefix}
        result = []
        while True:
            root = self.request('GET', params)
            for e in root:
                if tag(e) in ('Version', 'DeleteMarker'):
                    result.append(dict(fields(e), kind=tag(e)))
            v = fields(root)
            if v.get('IsTruncated') != 'true': return result
            params['key-marker'] = v['NextKeyMarker']
            if v.get('NextVersionIdMarker'): params['version-id-marker'] = v['NextVersionIdMarker']

def crypt(mode, names):
    result = {}
    for start in range(0, len(names), 10):
        batch = names[start:start+10]
        command = ['/usr/local/bin/rclone', 'cryptdecode'] + (['--reverse'] if mode == 'cryptencode' else [])
        out = subprocess.check_output([*command, 'idrive-crypt:', *batch, '--config', CONFIG], text=True)
        lines = out.splitlines()
        assert len(lines) == len(batch)
        for original, line in zip(batch, lines):
            result[original] = line.split()[-1]
    return result

def save(name, data):
    tmp = STATE/(name+'.tmp')
    tmp.write_text(json.dumps(data, indent=2)+'\n')
    os.replace(tmp, STATE/name)

def candidates(versions, decoded, local_names):
    bykey = collections.defaultdict(list)
    for item in versions: bykey[item['Key']].append(item)
    selected = []
    for key, entries in bykey.items():
        latest = [e for e in entries if e['IsLatest'] == 'true']
        assert len(latest) == 1
        if latest[0]['kind'] != 'DeleteMarker': continue
        name = decoded[key]
        assert re.fullmatch(r'homelab-proxmox-guests/vzdump-(?:lxc|qemu)-\d+-\d{4}_\d{2}_\d{2}-\d{2}_\d{2}_\d{2}\.(?:tar|vma)\.zst', name)
        assert name.split('/')[-1] not in local_names, 'Deleted cloud key still retained locally'
        for e in entries:
            if e['kind'] == 'Version':
                assert e['IsLatest'] == 'false'
                selected.append(e)
    return selected

def lifecycle(prefixes):
    root = ET.Element('LifecycleConfiguration', xmlns='http://s3.amazonaws.com/doc/2006-03-01/')
    for name, days in [('homelab-proxmox-guests',1),('gowest',30),('configuration',14),('home-assistant',14),('mac',14),('jellyfin',14),('paperless-service',14),('service-reconstruction',14)]:
        rule = ET.SubElement(root, 'Rule')
        ET.SubElement(rule, 'ID').text = 'noncurrent-'+name
        ET.SubElement(rule, 'Filter').append(ET.Element('Prefix'))
        rule.find('Filter/Prefix').text = prefixes[name]+'/'
        ET.SubElement(rule, 'Status').text = 'Enabled'
        exp = ET.SubElement(rule, 'NoncurrentVersionExpiration')
        ET.SubElement(exp, 'NoncurrentDays').text = str(days)
    rule = ET.SubElement(root, 'Rule')
    ET.SubElement(rule, 'ID').text = 'expired-delete-markers'
    ET.SubElement(rule, 'Filter')
    ET.SubElement(rule, 'Status').text = 'Enabled'
    ET.SubElement(ET.SubElement(rule, 'Expiration'), 'ExpiredObjectDeleteMarker').text = 'true'
    return ET.tostring(root)

def execute(s3):
    prefix = crypt('cryptencode', ['homelab-proxmox-guests'])['homelab-proxmox-guests']+'/'
    versions = s3.versions(prefix)
    decoded = crypt('cryptdecode', sorted({e['Key'] for e in versions}))
    local = Path('/srv/recovery/guests/homelab-proxmox-guests')
    assert Path('/srv/recovery/guests/.recovery-relay-source').read_text().strip() == 'Recovery/guests'
    local_names = {p.name for p in local.iterdir() if p.is_file()}
    assert len(local_names) >= 150
    selected = candidates(versions, decoded, local_names)
    assert len(selected) == EXPECTED_COUNT and sum(int(e['Size']) for e in selected) == EXPECTED_BYTES, 'Reviewed version set changed'
    before = sorted((e['Key'], e['VersionId'], e['Size']) for e in versions if e['kind']=='Version' and e['IsLatest']=='true')
    save('cleanup-20261007-manifest.json', {'versions':selected, 'current_before':before})
    assert s3.versions(prefix) == versions, 'Cloud inventory changed during planning'
    assert {p.name for p in local.iterdir() if p.is_file()} == local_names
    deleted = []
    for start in range(0, len(selected), 100):
        batch = selected[start:start+100]
        root = ET.Element('Delete', xmlns='http://s3.amazonaws.com/doc/2006-03-01/')
        for e in batch:
            o = ET.SubElement(root, 'Object')
            ET.SubElement(o,'Key').text=e['Key']; ET.SubElement(o,'VersionId').text=e['VersionId']
        response = s3.request('POST', {'delete':''}, ET.tostring(root))
        errors = [e for e in response if tag(e)=='Error']
        assert not errors, 'S3 reported partial delete error; inspect protected manifest'
        ack={(fields(e)['Key'],fields(e)['VersionId']) for e in response if tag(e)=='Deleted'}
        assert ack=={(e['Key'],e['VersionId']) for e in batch}
        deleted.extend(batch);save('cleanup-20261007-deleted.json',deleted)
    after=s3.versions(prefix)
    assert sorted((e['Key'],e['VersionId'],e['Size']) for e in after if e['kind']=='Version' and e['IsLatest']=='true')==before
    assert not [e for e in after if e['kind']=='Version' and e['IsLatest']=='false']
    names=['homelab-proxmox-guests','gowest','configuration','home-assistant','mac','jellyfin','paperless-service','service-reconstruction']
    try:
        prior=s3.request('GET',{'lifecycle':''})
    except RuntimeError as error:
        assert 'NoSuchLifecycleConfiguration' in str(error)
        prior=ET.Element('NoPriorLifecycle')
    assert tag(prior)=='NoPriorLifecycle', 'Unexpected lifecycle; do not overwrite'
    save('lifecycle-before.json',{'xml':ET.tostring(prior,encoding='unicode')})
    body=lifecycle(crypt('cryptencode',names))
    (STATE/'lifecycle-request.xml').write_bytes(body)
    s3.request('PUT',{'lifecycle':''},body)
    live=s3.request('GET',{'lifecycle':''})
    (STATE/'lifecycle-verified.xml').write_bytes(ET.tostring(live))
    expected=ET.fromstring(body)
    def norm(e):return (tag(e),(e.text or '').strip(),sorted([norm(x) for x in e]))
    assert norm(live)==norm(expected), 'Lifecycle readback mismatch'
    print(json.dumps({'deleted_versions':len(deleted),'deleted_bytes':sum(int(e['Size']) for e in deleted),'current_guest_versions_unchanged':len(before),'lifecycle_rules':len(live)}),flush=True)

def audit(s3):
    versions=s3.versions()
    groups=collections.defaultdict(lambda:dict(current_bytes=0,noncurrent_bytes=0,current_count=0,noncurrent_count=0,delete_markers=0))
    prefixes=crypt('cryptdecode',sorted({e['Key'].split('/')[0] for e in versions}))
    for e in versions:
        g=groups[prefixes[e['Key'].split('/')[0]]]
        if e['kind']=='DeleteMarker':g['delete_markers']+=1;continue
        kind='current' if e['IsLatest']=='true' else 'noncurrent'
        g[kind+'_bytes']+=int(e['Size']);g[kind+'_count']+=1
    current=sum(g['current_bytes'] for g in groups.values());old=sum(g['noncurrent_bytes'] for g in groups.values())
    result={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'current_bytes':current,'noncurrent_bytes':old,'total_bytes':current+old,'prefixes':dict(groups),'status':'warning' if current+old>1000000000000 or old>150000000000 else 'success'}
    save('usage.json',result)
    print(json.dumps(result),flush=True)
    return 0 if result['status']=='success' else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--execute-20261007',action='store_true');args=parser.parse_args()
    os.umask(0o077);STATE.mkdir(mode=0o700,parents=True,exist_ok=True)
    with open('/run/idrive-relay-sync.lock','w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        s3=S3()
        if args.execute_20261007:execute(s3)
        raise SystemExit(audit(s3))
