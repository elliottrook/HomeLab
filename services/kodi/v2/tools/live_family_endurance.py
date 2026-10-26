"""Repeat the private mixed-player soak while recording bounded HP health."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


SOAK=Path('/storage/.aster-staging/aster-family-mixed-soak1/live_family_mixed_soak.py')
RESULTS=SOAK.parent
LOG=Path('/storage/.kodi/temp/kodi.log')


def require(value,code):
    if not value: raise RuntimeError(code)


def result_files(): return set(RESULTS.glob('mixed-soak-*.json'))


def process():
    rows=[]
    for path in Path('/proc').glob('[0-9]*'):
        try:
            cmd=(path/'cmdline').read_bytes()
            if b'/usr/lib/kodi/kodi.bin' in cmd: rows.append(path)
        except OSError: pass
    require(len(rows)==1,'endurance-kodi-process'); return rows[0]


def metric():
    proc=process(); status=(proc/'status').read_text()
    rss=re.search(r'^VmRSS:\s+(\d+)\s+kB$',status,re.M)
    require(rss,'endurance-rss')
    thermal=Path('/sys/class/thermal/thermal_zone0/temp')
    temperature=int(thermal.read_text().strip())/1000 if thermal.is_file() else None
    return dict(pid=int(proc.name),rss_kib=int(rss.group(1)),temperature_c=temperature,
                timestamp_ns=time.time_ns())


def wait_result(before,timeout=35):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        found=result_files()-before
        if len(found)==1:
            value=json.loads(found.pop().read_text())
            require(value.get('passed') is True,'endurance-soak-failed'); return value
        require(not found,'endurance-result-count')
        time.sleep(.25)
    raise RuntimeError('endurance-soak-timeout')


def run(cycles,output):
    require(os.uname().nodename=='AsterTV' and type(cycles) is int and 1<=cycles<=20,
            'endurance-arguments')
    require(SOAK.is_file() and not SOAK.is_symlink(),'endurance-harness')
    output=Path(output); require(not output.exists(),'endurance-output-exists')
    start=metric(); log_offset=LOG.stat().st_size; crashes=len(tuple(Path('/storage').rglob('kodi_crashlog-*')))
    runs=[]
    for index in range(cycles):
        before=result_files()
        subprocess.run(['/usr/bin/kodi-send','--action=ActivateWindow(Home)'],check=True,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(.5)
        subprocess.run(['/usr/bin/kodi-send','--action=RunScript('+str(SOAK)+')'],check=True,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        result=wait_result(before); runs.append(dict(index=index+1,metric=metric(),
            result_timestamp_ns=result['timestamp_ns']))
    raw=LOG.read_bytes()[log_offset:].decode('utf-8','replace')
    findings=[line for line in raw.splitlines()
              if re.search(r'ERROR|FATAL|EXCEPTION|Kodi is not playing any file',line)]
    end=metric(); require(end['pid']==start['pid'],'endurance-kodi-restarted')
    require(len(tuple(Path('/storage').rglob('kodi_crashlog-*')))==crashes,'endurance-new-crash')
    require(not findings,'endurance-log-errors')
    require(not Path('/storage/.aster-recovery-required').exists(),'endurance-recovery-marker')
    value=dict(passed=True,cycles=cycles,start=start,end=end,runs=runs,
               crash_files=crashes,log_findings=0,
               harness_sha256=hashlib.sha256(SOAK.read_bytes()).hexdigest())
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_suffix('.tmp'); temporary.write_text(json.dumps(value,indent=2)+'\n')
    os.replace(temporary,output); return value


if __name__=='__main__':
    require(len(sys.argv)==3 and re.fullmatch(r'[1-9]|1\d|20',sys.argv[1]),'endurance-cli')
    print(json.dumps(run(int(sys.argv[1]),sys.argv[2]),sort_keys=True))
