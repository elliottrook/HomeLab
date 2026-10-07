#!/usr/bin/env python3
"""Read only the relay's aggregate report, never credentials or object names."""
import datetime
import json
import subprocess

def assess(data, now):
    age = (now-datetime.datetime.fromisoformat(data['checked_utc'])).total_seconds()/3600
    return (0 <= age < 30 and data['status']=='success'
            and data['total_bytes'] <= 1000000000000
            and data['noncurrent_bytes'] <= 150000000000), age

if __name__ == '__main__':
    try:
        result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','proxmox',
            'pct exec 112 -- cat /var/lib/idrive-version-maintenance/usage.json'],
            capture_output=True,text=True,timeout=20,check=True)
        data=json.loads(result.stdout)
        ok,age=assess(data,datetime.datetime.now(datetime.timezone.utc))
        print('{}: IDrive storage {:.1f} GB current + {:.1f} GB history; report {:.1f}h old'.format(
            'PASS' if ok else 'WARN',data['current_bytes']/1e9,data['noncurrent_bytes']/1e9,age))
        raise SystemExit(0 if ok else 1)
    except (OSError,subprocess.SubprocessError,ValueError,KeyError,TypeError):
        print('WARN: IDrive usage report unavailable or invalid')
        raise SystemExit(1)
