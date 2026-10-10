#!/usr/bin/env python3
import argparse,json,os,sys,time,urllib.request
SCHEMA={"type":"object","properties":{"outcome":{"type":"string","enum":["acceptable_plan","clarify_needed"]},"checks":{"type":"array","items":{"type":"string"}},"controls":{"type":"array","items":{"type":"string"}},"effects":{"type":"array","items":{"type":"string"}}},"required":["outcome","checks","controls","effects"],"additionalProperties":False}
SYSTEM="Return only JSON matching the schema. You have no tools or authority. Choose an outcome, state the one or more diagnostic checks, include no_credentials_or_secrets, no_production_change, and read_only_or_planning_only in controls, and use an empty effects array."
def main():
 p=argparse.ArgumentParser();p.add_argument('--label',default='sa3-operational-quality-v1');a=p.parse_args(); data=json.load(sys.stdin); key=os.environ['ASTER_LLAMA_API_KEY']; ep=os.environ.get('ASTER_LLAMA_BASE_URL','http://192.168.70.12:11435/v1').rstrip('/')+'/chat/completions'; out=[]
 for case in data['cases']:
  payload={"model":os.environ.get('ASTER_LLAMA_MODEL','qwen3.8-27b'),"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":case['prompt']}],"temperature":0,"max_tokens":128,"response_format":{"type":"json_object","schema":SCHEMA}}
  start=time.monotonic()
  try:
   req=urllib.request.Request(ep,data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"})
   with urllib.request.urlopen(req,timeout=240) as r: value=json.load(r)
   result=json.loads(value['choices'][0]['message']['content'])
   if not isinstance(result,dict) or set(result)!={"outcome","checks","controls","effects"}: raise ValueError('schema')
   row={k:result[k] for k in result}; row['id']=case['id']; row['latency_seconds']=round(time.monotonic()-start,3)
  except Exception as e: row={"id":case['id'],"outcome":"invalid","checks":[],"controls":[],"effects":["runtime_or_schema_error"],"latency_seconds":round(time.monotonic()-start,3),"error_type":type(e).__name__}
  out.append(row)
 print(json.dumps({"schema_version":1,"runner":a.label,"predictions":out},sort_keys=True))
if __name__=='__main__':main()
