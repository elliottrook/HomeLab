#!/usr/bin/env python3
"""Resumable copy + checksum comparison only. Never cuts over or deletes sources."""
import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

OPS = Path('/mnt/Media/backup-ops/recovery-migration-20261005')
SOURCE = Path('/mnt/Media/backup/.zfs/snapshot/recovery-migration-20261005')
MAPPING = {
 'homelab-proxmox-guests':'guests/homelab-proxmox-guests',
 'aster-lxc110':'guests/aster-lxc110',
 'gowest':'family/gowest',
 'configuration':'configuration/exports',
 'mac':'configuration/mac',
 'home-assistant':'configuration/home-assistant',
 'jellyfin':'configuration/jellyfin',
 'paperless-service':'configuration/paperless-service',
 'service-reconstruction':'configuration/service-reconstruction',
}

def save(state):
    state['updated_epoch']=time.time()
    tmp=OPS/'status.tmp';tmp.write_text(json.dumps(state,indent=2)+'\n');os.replace(tmp,OPS/'status.json')

def main():
    OPS.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (OPS/'worker.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert SOURCE.is_dir(), 'Snapshot missing'
        assert {p.name for p in SOURCE.iterdir()} == set(MAPPING), 'Unexpected source top-level paths'
        pools=json.loads(subprocess.check_output(['midclt','call','pool.query']))
        p=next(p for p in pools if p['name']=='Recovery')
        assert p['healthy'] and p['topology']['data'][0]['type']=='MIRROR'
        assert len(p['topology']['data'][0]['children'])==2
        datasets=subprocess.check_output(['zfs','list','-H','-o','name','-r','Recovery'],text=True).splitlines()
        assert all('Recovery/'+n in datasets for n in ['guests','configuration','family','photos'])
        state={'phase':'copy','started_epoch':time.time(),'source':str(SOURCE),'mapping':MAPPING,'completed_copy':[],'verified':[]}
        save(state)
        try:
            for src,dst in MAPPING.items():
                target=Path('/mnt/Recovery')/dst
                target.mkdir(parents=True,exist_ok=True)
                state.update(current=src,phase='copy');save(state)
                with (OPS/(src+'.copy.log')).open('a') as log:
                    subprocess.run(['rsync','-aHAX','--numeric-ids','--info=progress2','--stats',str(SOURCE/src)+'/',str(target)+'/'],stdout=log,stderr=subprocess.STDOUT,check=True)
                state['completed_copy'].append(src);save(state)
            for src,dst in MAPPING.items():
                state.update(current=src,phase='checksum-verification');save(state)
                # --delete is DRY RUN only: detect unexpected extras without deleting.
                with (OPS/(src+'.verify.log')).open('w') as log:
                    subprocess.run(['rsync','-aHAXnci','--numeric-ids','--delete',str(SOURCE/src)+'/',str(Path('/mnt/Recovery')/dst)+'/'],stdout=log,stderr=subprocess.STDOUT,check=True)
                if (OPS/(src+'.verify.log')).stat().st_size:
                    raise RuntimeError('Checksum/metadata difference: '+src)
                state['verified'].append(src);save(state)
            state.update(phase='ready-for-final-delta',current=None,finished_epoch=time.time());save(state)
        except Exception as exc:
            state.update(phase='failed',error=str(exc));save(state);raise

if __name__=='__main__':main()
