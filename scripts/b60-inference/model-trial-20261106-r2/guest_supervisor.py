"""Fixed wait-before-exec supervisor inside the candidate's private mount NS.

No model opens until the host has transferred the exact readonly candidate.
No arbitrary command, credential read, output or retry exists here.
"""
import argparse,os,stat,time
from fixed_command import BINARY,MODEL,start_command

def run(deadline):
 if os.getuid()!=999 or not time.time()<deadline<=time.time()+1800:raise RuntimeError('SUPERVISOR_IDENTITY')
 cutoff=min(deadline,time.time()+120)
 while time.time()<cutoff:
  try:
   info=os.stat(MODEL,follow_symlinks=False)
   if stat.S_ISREG(info.st_mode) and info.st_size==20419565568 and info.st_uid==999 and info.st_mode&0o777==0o400:
    command=start_command();index=command.index(BINARY);os.execv(BINARY,command[index:])
  except (FileNotFoundError,PermissionError):pass
  time.sleep(.2)
 raise RuntimeError('SUPERVISOR_MAPPING_DEADLINE')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--deadline',type=int,required=True);a=p.parse_args();run(a.deadline)
