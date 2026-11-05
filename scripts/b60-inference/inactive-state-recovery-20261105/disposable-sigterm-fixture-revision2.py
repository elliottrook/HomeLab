"""Disposable systemd-only state test; never runs a production job or model."""
import subprocess,sys,time,json
from pathlib import Path
sys.path.insert(0,'/root/b60-inactive-state-operational-20261105-v2/payload/candidate/exclusive-session')
import lab_hours_unit_adapter as module
name='b60-inactive-sigterm-fixture-20261105.service';path=Path('/etc/systemd/system')/name
assert not path.exists()
def call(cmd):return subprocess.run(cmd,capture_output=True,text=True,timeout=15)
def fields():
 p=call(['systemctl','show',name,'--property=ActiveState,Result,ExecMainCode,ExecMainStatus,MainPID,TasksCurrent,ExecMainStartTimestampMonotonic']);assert p.returncode==0
 return dict(line.split('=',1) for line in p.stdout.splitlines())
try:
 path.write_text('[Unit]\nDescription=Disposable B60 inactive state fixture\n[Service]\nType=oneshot\nExecStart=/usr/bin/sleep 60\n');path.chmod(0o644)
 assert call(['systemctl','daemon-reload']).returncode==0
 assert call(['systemctl','start','--no-block',name]).returncode==0
 for _ in range(20):
  if fields()['MainPID']!='0':break
  time.sleep(.1)
 assert fields()['MainPID']!='0'
 assert call(['systemctl','kill','--signal=TERM',name]).returncode==0
 for _ in range(30):
  if fields()['ActiveState']=='failed':break
  time.sleep(.1)
 before=fields();assert before['Result']=='signal' and before['ExecMainStatus']=='15' and before['ExecMainCode']=='2' and before['MainPID']=='0'
 module.SCOPE.add(('115',name))
 commands=[]
 def runner(cmd,timeout):
  assert cmd[:5]==('pct','exec','115','--','systemctl')
  commands.append(cmd[5:]);p=subprocess.run(['systemctl',*cmd[5:]],capture_output=True,text=True,timeout=timeout);return p.returncode,p.stdout
 adapter=module.ProxmoxUnitAdapter(runner)
 row={'guest':'115','unit':name,'active':'inactive','enablement':'static'}
 # The production adapter normally validates a complete capture. Use the
 # single disposable fixture as its entire synthetic scope, with exact row schema.
 module.SCOPE={('115',name)}
 snapshot=[row]
 adapter.restore(snapshot,time.time()+30,configuration_restored=True,timer_resume_safe=lambda *a:True)
 after=fields();assert after['ActiveState']=='inactive'
 assert after['MainPID']=='0'
 assert after['ExecMainStartTimestampMonotonic'] in {'0','',before['ExecMainStartTimestampMonotonic']}
 assert not any(args[0]=='start' for args in commands)
 assert adapter.cleared_failures[0]['state_reset']=='observed-inactive'
 print(json.dumps({'state':'disposable-SIGTERM-reset-pass','production_job_started':False,'model_called':False,'only_stop_and_reset_commands':True,'zero_process_after_reset':True,'events':adapter.cleared_failures}))
finally:
 call(['systemctl','stop',name]);call(['systemctl','reset-failed',name]);path.unlink(missing_ok=True);call(['systemctl','daemon-reload'])
