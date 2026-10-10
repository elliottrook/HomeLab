"""Fixed guarded cleanup proposal; typed ownership data only, no execution entry."""
import json
import re
from s0_lxc100_observe import BOUNDED_SOURCE, parse_canary
from s0_probe_state import envelope
from s0_feasibility_supervisor import remote_args

SOURCE=BOUNDED_SOURCE+r'''
import json,os,stat,sys
receipt=json.loads(sys.argv[1]); assert receipt['completed'] is True
p='/var/tmp/aster-s0-feasibility-20260926'
unit='aster-s0-feasibility-20260926.service'
raw=bounded(['/usr/bin/systemctl','show',unit,'-p','LoadState','-p','ActiveState','-p','MainPID','-p','InvocationID'])
values={}
for line in raw.decode().splitlines():
 k,sep,v=line.partition('=');assert sep and k not in values;values[k]=v
assert set(values)=={'LoadState','ActiveState','MainPID','InvocationID'}
assert values['MainPID']=='0' and values['ActiveState']=='inactive'
if values['LoadState']=='not-found':assert values['InvocationID']==''
else:assert values['LoadState']=='loaded' and values['InvocationID']==receipt['invocation_id']
assert not os.path.exists('/sys/fs/cgroup/system.slice/'+unit)
assert not os.path.lexists('/usr/aster-s0-feasibility-denied')
d=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
try:
 s=os.fstat(d); saved=receipt['canary']
 assert (s.st_dev,s.st_ino)==(saved['directory_dev'],saved['directory_inode'])
 assert s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o755 and os.listdir(d)==['canary']
 f=os.open('canary',os.O_RDONLY|os.O_NOFOLLOW,dir_fd=d)
 try:
  t=os.fstat(f)
  assert (t.st_dev,t.st_ino)==(saved['file_dev'],saved['file_inode'])
  assert stat.S_ISREG(t.st_mode) and t.st_uid==0 and t.st_nlink==1 and stat.S_IMODE(t.st_mode)==0o644
  assert os.read(f,2)==b'x'
  again=os.stat('canary',dir_fd=d,follow_symlinks=False)
  assert (again.st_dev,again.st_ino)==(t.st_dev,t.st_ino)
  os.unlink('canary',dir_fd=d)
 finally:os.close(f)
 current=os.lstat(p);assert (current.st_dev,current.st_ino)==(s.st_dev,s.st_ino)
 os.rmdir(p)
finally:os.close(d)
print('{"removed_owned_canary":true}')
'''


def argv(receipt):
    if type(receipt) is not dict or set(receipt)!={'canary','invocation_id','main_pid','completed'}:raise ValueError('receipt schema')
    parse_canary(envelope(receipt['canary']))
    if type(receipt['invocation_id']) is not str or not re.fullmatch('[0-9a-f]{32}',receipt['invocation_id']):raise ValueError('invocation')
    if type(receipt['main_pid']) is not int or not 0<receipt['main_pid']<2**31 or receipt['completed'] is not True:raise ValueError('completion required')
    if any(v>=2**64 for v in receipt['canary'].values()):raise ValueError('stat bounds')
    return remote_args(['/usr/bin/python3.13','-I','-S','-B','-c',SOURCE,json.dumps(receipt,sort_keys=True,separators=(',',':'))])
