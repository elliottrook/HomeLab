#!/usr/bin/env python3
"""Temporary native GenAI adapter: synthetic-only, not production API parity.

Single request, 8K total tokens, <=256 new tokens, greedy reasoning-off, no MTP,
no prefix cache, no tools/streaming/media. Model inference explicitly GPU only.
Existing service keys are read only in guest memory and never logged/persisted.
"""
import argparse
import hmac
from http.server import BaseHTTPRequestHandler,HTTPServer
import json
import math
import os
from pathlib import Path
import sys
import time

RAM=Path('/dev/shm/b60-openvino-runtime-20261011')
MODEL='/opt/b60-openvino-trial-20261011/model'
def validate_payload(p):
 if not isinstance(p,dict):raise ValueError('object required')
 if p.get('stream') or p.get('tools') or p.get('tool_choice'):raise ValueError('unsupported API feature')
 if p.get('temperature',0)!=0:raise ValueError('greedy trial only')
 messages=p.get('messages');assert isinstance(messages,list) and 1<=len(messages)<=8
 assert all(isinstance(m,dict) and m.get('role') in ['system','user','assistant'] and isinstance(m.get('content'),str) for m in messages)
 tokens=p.get('max_tokens',128);assert type(tokens) is int and 1<=tokens<=256
 fmt=p.get('response_format')
 if fmt:assert fmt.get('type')=='json_schema' and isinstance(fmt.get('json_schema',{}).get('schema'),dict)
 return messages,tokens,fmt
def metric_response(result,max_new_tokens=256):
 metrics=result.perf_metrics
 n=int(metrics.get_num_generated_tokens());prompt_n=int(metrics.get_num_input_tokens())
 rate=float(metrics.get_throughput().mean);ttft=float(metrics.get_ttft().mean)
 assert n>0 and math.isfinite(rate) and rate>0 and math.isfinite(ttft) and ttft>=0
 assert len(result.texts)==1
 return {'choices':[{'index':0,'message':{'role':'assistant','content':result.texts[0]},'finish_reason':'length' if n==max_new_tokens else 'stop'}],
         'usage':{'prompt_tokens':prompt_n,'completion_tokens':n,'total_tokens':prompt_n+n},
         'timings':{'predicted_per_second':rate,'predicted_n':n,'prompt_n':prompt_n,'openvino_ttft_ms':ttft},
         'trial_metadata':{'runtime':'native OpenVINO GenAI 2026.4','quantization':'vendor INT4_ASYM group128','mtp':False,'prefix_cache':False,'reasoning':False,'decode_metric':'PerfMetrics.get_throughput().mean','prefill_time_unavailable':True,'production_api_parity':False}}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');a=p.parse_args();assert a.execute
 assert (RAM/'consent/intel/openvino_telemetry').read_text()=='0'
 sys.path.insert(0,str(RAM/'site'))
 # Source-supported checker, redirected only in this process to private declined
 # consent. No home directory/configuration or opt-out network event is touched.
 from openvino_telemetry.utils.opt_in_checker import OptInChecker,ConsentCheckResult
 OptInChecker.consent_file_base_dir=staticmethod(lambda:str(RAM/'consent'))
 assert OptInChecker().check(False)==ConsentCheckResult.DECLINED
 import openvino as ov
 import openvino_genai as genai
 core=ov.Core();devices=core.available_devices
 assert 'GPU' in devices or 'GPU.0' in devices
 name=core.get_property('GPU','FULL_DEVICE_NAME');assert 'B60' in name
 print(json.dumps({'native_runtime':ov.__version__,'gpu_name':name,'explicit_device':'GPU','cpu_model_fallback':False}),flush=True)
 scheduler=genai.SchedulerConfig();scheduler.cache_size=1;scheduler.max_num_seqs=1;scheduler.max_num_batched_tokens=8192;scheduler.enable_prefix_caching=False
 load=time.monotonic()
 pipeline=genai.VLMPipeline(MODEL,'GPU',scheduler_config=scheduler)
 tokenizer=pipeline.get_tokenizer()
 keys=[s.strip() for s in Path('/etc/aster-llama-api-keys').read_text().splitlines() if s.strip()]
 assert keys
 print(json.dumps({'native_ready':True,'load_seconds':time.monotonic()-load,'context_total_tokens':8192,'mtp':False,'reasoning':False,'prefix_cache':False}),flush=True)
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def setup(self):super().setup();self.connection.settimeout(15)
  def send(self,status,payload):
   raw=json.dumps(payload).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  def authorized(self):
   header=self.headers.get('Authorization','')
   return any(hmac.compare_digest(header,'Bearer '+key) for key in keys)
  def do_GET(self):
   if self.path=='/health':self.send(200,{'status':'ok'})
   elif not self.authorized():self.send(401,{'error':'unauthorized'})
   elif self.path=='/v1/models':self.send(200,{'data':[{'id':'local-model','object':'model'}]})
   else:self.send(404,{'error':'unsupported trial endpoint'})
  def do_POST(self):
   if not self.authorized():self.send(401,{'error':'unauthorized'});return
   try:
    length=int(self.headers.get('Content-Length','0'));assert 0<length<=128*1024
    payload=json.loads(self.rfile.read(length))
    if self.path=='/tokenize':
     assert isinstance(payload.get('content'),str)
     ids=tokenizer.encode(payload['content'],add_special_tokens=False).input_ids.data.reshape(-1).tolist()
     self.send(200,{'tokens':ids});return
    assert self.path=='/v1/chat/completions'
    messages,tokens,fmt=validate_payload(payload)
    prompt=tokenizer.apply_chat_template(messages,True,extra_context={'enable_thinking':False})
    assert '<think>\n\n</think>' in prompt.rsplit('<|im_start|>assistant',1)[-1], 'reasoning-off template not proven'
    ids=tokenizer.encode(prompt,add_special_tokens=False).input_ids.data
    assert ids.size+tokens<=8192,'context bound'
    config=genai.GenerationConfig(Path(MODEL)/'generation_config.json')
    config.max_new_tokens=tokens;config.do_sample=False;config.apply_chat_template=False
    if fmt:config.structured_output_config=genai.StructuredOutputConfig(json_schema=json.dumps(fmt['json_schema']['schema']))
   except Exception as exc:
    self.send(400,{'error':type(exc).__name__});return
   try:
    deadline=time.monotonic()+90
    def streamer(text):return genai.StreamingStatus.CANCEL if time.monotonic()>deadline else genai.StreamingStatus.RUNNING
    result=pipeline.generate(prompt,images=[],generation_config=config,streamer=streamer)
    assert time.monotonic()<deadline,'generation bound'
    self.send(200,metric_response(result,tokens))
   except BaseException as exc:
    self.send(500,{'error':type(exc).__name__})
    print(json.dumps({'native_failure':type(exc).__name__,'automatic_retry':False}),flush=True)
    os._exit(2)
 server=HTTPServer(('192.168.70.12',11435),Handler);server.serve_forever()
if __name__=='__main__':main()
