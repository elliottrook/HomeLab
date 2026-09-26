"""Fixed LXC100 observation catalogue/parsers. Live entry is permanently denied.

Source strings are proposed root-side metadata collectors, never executed at import
or during local tests. They do not read accepted pilot data or credentials.
"""
import hashlib
import json
import re
from pathlib import Path

import s0_feasibility_supervisor as supervisor
from s0_probe_state import EXPECTED, decode, health
from validate_label_batch import exact, reject

UNIT=supervisor.UNIT
PROPERTIES=('LoadState','ActiveState','SubState','MainPID','InvocationID','ControlGroup',
            'DynamicUser','NoNewPrivileges','PrivateNetwork','ProtectSystem','InaccessiblePaths',
            'SystemCallFilter','MemoryMax','MemorySwapMax','TasksMax','RuntimeMaxUSec','KillMode',
            'ExecMainCode','ExecMainStatus','Result','Environment','UnsetEnvironment')
# These strings are fixed proposals, not remotely executed by this module.
BOUNDED_SOURCE="import os,selectors,signal,subprocess,time\n_end=time.monotonic()+12\n\ndef bounded(argv):\n p=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True,env={'LANG':'C','LC_ALL':'C'})\n sel=selectors.DefaultSelector(); chunks={'out':bytearray(),'err':bytearray()}; total=0\n try:\n  for stream,key in ((p.stdout,'out'),(p.stderr,'err')):\n   os.set_blocking(stream.fileno(),False);sel.register(stream,selectors.EVENT_READ,key)\n  while sel.get_map():\n   if time.monotonic()>=_end:raise TimeoutError('collector deadline')\n   for key,_ in sel.select(min(.05,max(0,_end-time.monotonic()))):\n    data=os.read(key.fileobj.fileno(),1024)\n    if not data:sel.unregister(key.fileobj);continue\n    total+=len(data)\n    if total>4096:raise ValueError('collector output limit')\n    chunks[key.data].extend(data)\n  p.wait(timeout=max(.001,_end-time.monotonic()))\n  if p.returncode or chunks['err']:raise ValueError('collector command failed')\n  return bytes(chunks['out'])\n finally:\n  sel.close()\n  if p.poll() is None:\n   try:os.killpg(p.pid,signal.SIGKILL)\n   except ProcessLookupError:pass\n  p.wait(timeout=2);p.stdout.close();p.stderr.close()\n"
HEALTH_SOURCE=BOUNDED_SOURCE+r'''
import json,pathlib
names=bounded(['/usr/bin/docker','ps','-a','--format','{{.Names}}']).decode().splitlines()
expected={'homarr','authentik-homarr-ingress','authentik-code-ingress','code-server','beszel','homepage','beszel-agent','pihole','portainer'}
assert set(names)==expected and len(names)==len(expected)
containers={}
for name in sorted(expected):
 r=bounded(['/usr/bin/docker','inspect','--format','{{.State.Running}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}',name])
 assert len(r)<128
 run,h,n=r.decode().strip().split(); assert run in ('true','false')
 containers[name]={'running':run=='true','health':h,'restarts':int(n)}
host=bounded(['/usr/bin/systemctl','is-system-running'])
assert host==b'running\n'
mem=pathlib.Path('/proc/meminfo').read_text(); available=int(next(x.split()[1] for x in mem.splitlines() if x.startswith('MemAvailable:')))*1024
root=pathlib.Path('/sys/fs/cgroup'); current=int((root/'memory.current').read_text()); maximum=int((root/'memory.max').read_text())
psi=(root/'memory.pressure').read_text(); some=next(x for x in psi.splitlines() if x.startswith('some ')); avg=float(next(x.split('=')[1] for x in some.split() if x.startswith('avg10=')))
print(json.dumps({'host':'running','pihole':containers['pihole'],'containers':containers,'guest_mem_available':available,'cgroup_memory_current':current,'cgroup_memory_max':maximum,'memory_psi_some_avg10':avg}))
'''
PATH_SOURCE=r'''import os,json
print(json.dumps({'canary_directory_absent':not os.path.lexists('/var/tmp/aster-s0-feasibility-20260926'),'runtime_probe_absent':not os.path.lexists('/usr/aster-s0-feasibility-denied')}))
'''
CANARY_SOURCE=r'''import os,stat,json
p='/var/tmp/aster-s0-feasibility-20260926'; s=os.lstat(p)
assert stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o755
assert os.listdir(p)==['canary']
f=os.open(p+'/canary',os.O_RDONLY|os.O_NOFOLLOW); t=os.fstat(f)
assert stat.S_ISREG(t.st_mode) and t.st_uid==0 and t.st_nlink==1 and stat.S_IMODE(t.st_mode)==0o644
assert os.read(f,2)==b'x';os.close(f)
print(json.dumps({'directory_dev':s.st_dev,'directory_inode':s.st_ino,'file_dev':t.st_dev,'file_inode':t.st_ino,'directory_mode':stat.S_IMODE(s.st_mode),'file_mode':stat.S_IMODE(t.st_mode)}))
'''
CGROUP_SOURCE=BOUNDED_SOURCE+r'''
import pathlib,json
r=bounded(['/usr/bin/systemctl','show','aster-s0-feasibility-20260926.service','-p','ControlGroup','--value'])
group=r.decode().strip(); assert group=='/system.slice/aster-s0-feasibility-20260926.service'
root=pathlib.Path('/sys/fs/cgroup')/group.lstrip('/')
print(json.dumps({'control_group':group,'memory_max':int((root/'memory.max').read_text()),'memory_swap_max':int((root/'memory.swap.max').read_text()),'pids_max':int((root/'pids.max').read_text())}))
'''
ABSENCE_SOURCE=r'''import os,json
print(json.dumps({'directory_absent':not os.path.lexists('/var/tmp/aster-s0-feasibility-20260926'),'runtime_probe_absent':not os.path.lexists('/usr/aster-s0-feasibility-denied'),'cgroup_absent':not os.path.exists('/sys/fs/cgroup/system.slice/aster-s0-feasibility-20260926.service')}))
'''


def command_catalog():
    proposal=supervisor.command_proposal()
    commands=dict(proposal['commands'])
    commands['create-owned-canary']=supervisor.remote_args(['/usr/bin/python3.13','-I','-S','-B','-c',supervisor.CREATE_SOURCE+'\n'+CANARY_SOURCE])
    for key,source in {'health':HEALTH_SOURCE,'paths':PATH_SOURCE,'canary-stat':CANARY_SOURCE,
                       'cgroup':CGROUP_SOURCE,'absence':ABSENCE_SOURCE}.items():
        commands[key]=supervisor.remote_args(['/usr/bin/python3.13','-I','-S','-B','-c',source])
    commands['unit-properties']=supervisor.remote_args(['/usr/bin/systemctl','show',UNIT,
                                                       *sum((['-p',p] for p in PROPERTIES),[])])
    return commands


def catalog_digest():
    from s0_owned_cleanup import SOURCE
    return hashlib.sha256(json.dumps({'commands':command_catalog(),'guarded_cleanup_source':SOURCE},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def require_pinned_catalog(expected):
    reject(type(expected) is not str or expected!=catalog_digest(),'catalog pin mismatch')


def parse_properties(response):
    exact(response,{'returncode','stdout','stderr'})
    reject(type(response['returncode']) is not int or response['returncode']!=0 or
           type(response['stdout']) is not bytes or response['stderr']!=b'' or
           len(response['stdout'])>8192,'property command failed')
    result={}
    for line in response['stdout'].decode('utf-8').splitlines():
        key,sep,value=line.partition('=')
        reject(not sep or key not in PROPERTIES or key in result,'unexpected property')
        result[key]=value
    exact(result,PROPERTIES)
    return result


def parse_running(response,cgroup_response):
    values=parse_properties(response);cgroup=decode(cgroup_response)
    exact(cgroup,{'control_group','memory_max','memory_swap_max','pids_max'})
    reject(values['LoadState']!='loaded' or values['ActiveState']!='active' or
           values['SubState']!='running','unit not running')
    reject(not re.fullmatch('[1-9][0-9]*',values['MainPID']),'invalid PID')
    reject(not re.fullmatch('[0-9a-f]{32}',values['InvocationID']),'invalid invocation')
    expected_group='/system.slice/'+UNIT
    reject(values['ControlGroup']!=expected_group or cgroup['control_group']!=expected_group,'unexpected cgroup')
    for name in ('DynamicUser','NoNewPrivileges','PrivateNetwork'):
        reject(values[name]!='yes','boolean restriction not applied')
    reject(values['ProtectSystem']!='strict' or values['KillMode']!='control-group','unit restriction')
    reject(set(values['InaccessiblePaths'].split())!=set(EXPECTED['inaccessible_paths']),'path restriction')
    for key,target in [('MemoryMax',67108864),('MemorySwapMax',0),('TasksMax',1)]:
        reject(not values[key].isdigit() or int(values[key])!=target,'unit resource limit')
    # systemctl renders times as durations; allow only exact equivalent spellings.
    reject(values['RuntimeMaxUSec'] not in ('15s','15000000'),'runtime limit')
    for key,target in [('memory_max',67108864),('memory_swap_max',0),('pids_max',1)]:
        reject(type(cgroup[key]) is not int or cgroup[key]!=target,'kernel resource limit')
    reject(set(values['Environment'].split())!={'LANG=C','LC_ALL=C'},'fixed environment missing')
    expected_unset=next(x.split('=',1)[1].split() for x in supervisor.PROPERTIES if x.startswith('UnsetEnvironment='))
    reject(set(values['UnsetEnvironment'].split())!=set(expected_unset),'environment unset mismatch')
    syscall=values['SystemCallFilter'].split()
    reject(not syscall or not syscall[0].startswith('~'),'syscall deny-list not applied')
    names={x.lstrip('~') for x in syscall}
    reject(not {'@network-io','@mount','clone','clone3','fork','vfork'}<=names,'syscall restriction unverified')
    # Do not infer aliases/expanded groups; an unexpected display is inconclusive.
    return {'main_pid':int(values['MainPID']),'invocation_id':values['InvocationID'],
            'properties':dict(EXPECTED)}


def parse_health(response):
    value=decode(response);health(value);return value


def parse_canary(response):
    value=decode(response)
    exact(value,{'directory_dev','directory_inode','file_dev','file_inode','directory_mode','file_mode'})
    reject(any(type(v) is not int or v<0 for v in value.values()),'bad stat')
    reject(value['directory_mode']!=0o755 or value['file_mode']!=0o644,'mode mismatch')
    return value


def same_canary(first,current):
    return first==current


def live_entry(*_,**__):
    raise PermissionError('LXC100 transport entry disabled pending final review')


def parse_absence(response):
    value=decode(response);exact(value,{'directory_absent','runtime_probe_absent','cgroup_absent'})
    reject(any(type(v) is not bool for v in value.values()),'invalid absence observation')
    return value


def bind_ownership(creation_response, canary_response, ready, unit_response, cgroup_response):
    """Build a receipt only from successful own creation and own pipe readiness.

    Still a candidate: concurrent same-name unit replacement must be excluded by
    MainPID matching the worker-reported PID before any live ownership claim.
    """
    exact(creation_response,{'returncode','stdout','stderr'})
    reject(type(creation_response['returncode']) is not int or creation_response['returncode']!=0 or
           creation_response['stdout']!=b'' or creation_response['stderr']!=b'','creation not confirmed')
    canary=parse_canary(canary_response)
    exact(ready,{'scope','phase','checks','pid'})
    reject(ready['scope']!='invented-fixture-only' or ready['phase']!='ready' or
           type(ready['pid']) is not int or ready['pid']<1,'wrong readiness')
    from s0_probe_state import CHECKS
    exact(ready['checks'],CHECKS);reject(any(v is not True for v in ready['checks'].values()),'denial failed')
    running=parse_running(unit_response,cgroup_response)
    reject(running['main_pid']!=ready['pid'],'worker identity race')
    return {'canary':canary,'invocation_id':running['invocation_id'],'main_pid':running['main_pid']}


def cleanup_allowed(receipt, canary_response, unit_response, absence_response):
    """No live delete is performed; stop/recovery commands require same invocation."""
    canary=parse_canary(canary_response);unit=parse_properties(unit_response);absence=parse_absence(absence_response)
    return (same_canary(receipt['canary'],canary) and unit['InvocationID']==receipt['invocation_id']
            and unit['MainPID']=='0' and unit['ActiveState']=='inactive' and absence['cgroup_absent'])
