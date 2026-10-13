#!/usr/bin/env python3
"""Read-only B60 fd inventory; permit only the selected LXC 110 unit PID."""
import argparse
import json
import os
from pathlib import Path
import subprocess

def expected_client(namespace_pids,guest_pid,root_identity,guest_root):
    return bool(namespace_pids) and namespace_pids[-1]==guest_pid and root_identity==guest_root
def check(unit):
    assert unit in ['aster-llama.service','aster-b60-candidate.service']
    guest_pid=int(subprocess.check_output(['pct','exec','110','--','systemctl','show',unit,'-p','MainPID','--value'],text=True,timeout=30))
    assert guest_pid>1
    init=int(subprocess.check_output(['lxc-info','-n','110','-p','-H'],text=True,timeout=30))
    root=os.stat('/proc/'+str(init)+'/root');guest_root=(root.st_dev,root.st_ino)
    devices={p.name for p in Path('/sys/bus/pci/devices/0000:04:00.0/drm').iterdir() if p.name.startswith(('renderD','card'))}
    assert devices
    clients=[]
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():continue
        try:
            opened=any(Path(os.readlink(fd)).name in devices and os.readlink(fd).startswith('/dev/dri/') for fd in (process/'fd').iterdir())
            if not opened:continue
            line=next(l for l in (process/'status').read_text().splitlines() if l.startswith('NSpid:'))
            pids=[int(v) for v in line.split()[1:]];st=os.stat(process/'root')
            assert expected_client(pids,guest_pid,(st.st_dev,st.st_ino),guest_root),'unexpected B60 client'
            clients.append(int(process.name))
        except (FileNotFoundError,ProcessLookupError):continue
    return {'unexpected_clients':False,'selected_unit':unit,'client_count':len(clients)}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--unit',default='aster-llama.service')
    print(json.dumps(check(parser.parse_args().unit)))
