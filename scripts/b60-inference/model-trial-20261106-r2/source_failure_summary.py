"""Source-local fixed-field failure classification; never export logs or text."""
import json,re,subprocess,hashlib,time
from pathlib import Path
B='b60-exclusive-20261106-day-r2';ROOT=Path('/var/lib/local-ai-lab');S=ROOT/'exclusive-sessions'/B
state=json.loads((S/'session.json').read_bytes());assert state['phase']=='released'
assert not (ROOT/'lease.lock').exists() and not Path('/run/local-ai-lab-operation.lock').exists()
unit='b60-exclusive-trial-'+B+'.service'
def call(a):
 p=subprocess.run(a,capture_output=True,text=True,timeout=20);assert p.returncode==0;return p.stdout
raw=call(['pct','exec','110','--','journalctl','-u',unit,'--no-pager','-o','cat','-n','1500'])
statuses=[];timings=[];token_limits=[];error_counts={k:0 for k in ('sycl_device_error','oom','parse_error','request_error')}
for line in raw.splitlines():
 low=line.lower()
 clean=re.sub(r'\x1b\[[0-9;]*m','',line)
 if 'POST /v1/chat/completions' in clean:
  matches=re.findall(r'(?<![0-9.])([1-5][0-9]{2})(?![0-9.])',clean)
  if matches:statuses.append(int(matches[-1]))
 if 'eval time' in low:
  m=re.search(r'(prompt eval|eval) time\s*=\s*([0-9.]+) ms\s*/\s*([0-9]+) tokens?',line)
  if m:timings.append({'kind':m.group(1),'milliseconds':float(m.group(2)),'tokens':int(m.group(3))})
 for key in ('n_predict','n_decoded'):
  m=re.search(r'\b'+key+r'\s*[=:]\s*(\d+)',line)
  if m:token_limits.append({'key':key,'value':int(m.group(1))})
 if any(x in low for x in ('ur_result_error_device_lost','device lost','sycl exception','pi_error')):error_counts['sycl_device_error']+=1
 if any(x in low for x in ('out of memory','oom-kill','bad_alloc')):error_counts['oom']+=1
 if 'parse' in low and any(x in low for x in ('error','failed','invalid')):error_counts['parse_error']+=1
 if 'request' in low and any(x in low for x in ('error','failed')):error_counts['request_error']+=1
kernel=call(['journalctl','-k','--since','@1793990160','--until','@'+str(state['updated_epoch']),'--no-pager','-o','cat'])
bad=[l for l in kernel.lower().splitlines() if ('out of memory' in l or 'oom-kill' in l or ('xe ' in l and any(x in l for x in ('reset','hang','wedged','device lost','fault'))))]
print(json.dumps({'schema':'b60-model-source-failure-summary.v1','booking_id':B,'observed_epoch':int(time.time()),'journal_content_exported':False,'journal_sha256':hashlib.sha256(raw.encode()).hexdigest(),'http_statuses':statuses,'timings':timings,'token_limit_metadata':token_limits,'error_counts':error_counts,'kernel_hazard_count':len(bad),'request_script_exit_was_nonzero':True,'partial_answer_or_reasoning_retained':False},sort_keys=True))
