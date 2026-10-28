"""HP localhost-only, on-demand one-camera image viewer. No disk image cache."""
from datetime import datetime,timezone
import hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import selectors
import subprocess
import threading
import time
from urllib.parse import urlsplit,parse_qs

ROOT=Path('/storage/.aster-camera')
MAX_IMAGE=2097152

def fetch_frame():
    argv=['/usr/bin/ssh','-F','/dev/null','-T','-o','BatchMode=yes','-o','IdentitiesOnly=yes',
        '-o','IdentityAgent=none','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(ROOT/'known_hosts'),
        '-o','GlobalKnownHostsFile=/dev/null','-o','UpdateHostKeys=no','-o','PasswordAuthentication=no',
        '-o','KbdInteractiveAuthentication=no','-o','ConnectTimeout=3','-o','ConnectionAttempts=1',
        '-o','ClearAllForwardings=yes','-o','ForwardAgent=no','-i',str(ROOT/'id_ed25519'),
        'jelliott@192.168.20.10','aster-camera-front-v1']
    process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    output=bytearray();selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ)
    deadline=time.monotonic()+8
    try:
        while time.monotonic()<deadline:
            events=selector.select(min(.25,max(0,deadline-time.monotonic())))
            if not events:continue
            block=os.read(process.stdout.fileno(),min(65536,MAX_IMAGE+1-len(output)))
            if not block:break
            output.extend(block)
            if len(output)>MAX_IMAGE:raise ValueError('camera-image-too-large')
        else:raise ValueError('camera-fetch-timeout')
        if process.wait(timeout=1)!=0:raise ValueError('camera-fetch-failed')
        raw=bytes(output)
        if not 4<len(raw)<=MAX_IMAGE or not raw.startswith(b'\xff\xd8') or not raw.endswith(b'\xff\xd9'):raise ValueError('camera-image-invalid')
        return raw
    finally:
        selector.close();process.stdout.close()
        if process.poll() is None:process.kill();process.wait(timeout=2)

class Viewer:
    def __init__(self,fetch=fetch_frame,clock=time.monotonic):
        self.fetch=fetch;self.clock=clock;self.lock=threading.Lock();self.deadline=0
        self.frame=b'';self.last_fetch=0;self.frames=0;self.failures=0;self.last_frame_at='';self.frame_sha256=''
    def active(self):
        active=0<self.clock()<self.deadline
        if not active:self.frame=b''
        return active
    def start(self):
        with self.lock:
            self.deadline=self.clock()+300;self.frame=b'';self.last_fetch=0;self.failures=0
            return self.status_locked()
    def stop(self):
        with self.lock:
            self.deadline=0;self.frame=b'';return self.status_locked()
    def status_locked(self):
        active=self.active()
        return dict(ready=True,active=active,seconds_remaining=max(0,int(self.deadline-self.clock())) if active else 0,
                    frames=self.frames,failures=self.failures,last_frame_at=self.last_frame_at,frame_sha256=self.frame_sha256)
    def status(self):
        with self.lock:return self.status_locked()
    def expire(self):
        if self.lock.acquire(blocking=False):
            try:self.active()
            finally:self.lock.release()
    def image(self):
        with self.lock:
            if not self.active():raise ValueError('camera-view-not-active')
            if self.frame and self.clock()-self.last_fetch<1.8:return self.frame
            try:raw=self.fetch()
            except Exception:
                self.failures+=1;self.deadline=0;self.frame=b'';raise ValueError('camera-view-unavailable') from None
            if not self.active():raise ValueError('camera-view-expired')
            self.frame=raw;self.frames+=1;self.last_fetch=self.clock()
            self.last_frame_at=datetime.now(timezone.utc).isoformat();self.frame_sha256=hashlib.sha256(raw).hexdigest()
            return raw

class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.0'
    def log_message(self,*_args):pass
    def allowed(self):
        return self.client_address[0]=='127.0.0.1' and self.headers.get('Host')=='127.0.0.1:15102' and not self.headers.get('Origin') and not self.headers.get('X-Forwarded-For') and len(self.path)<=160
    def reply(self,status,raw,kind='application/json'):
        self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store, max-age=0');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
    def do_GET(self):
        if not self.allowed():self.reply(403,b'{"ok":false}');return
        parsed=urlsplit(self.path)
        if parsed.path=='/status' and not parsed.query:self.reply(200,json.dumps(self.server.viewer.status()).encode());return
        query=parse_qs(parsed.query)
        if parsed.path!='/api/front_of_house/latest.jpg' or set(query)-{'frame'} or any(not v.isdecimal() or len(v)>15 for values in query.values() for v in values):
            self.reply(404,b'{"ok":false}');return
        try:self.reply(200,self.server.viewer.image(),'image/jpeg')
        except ValueError:self.reply(503,b'{"ok":false,"code":"camera-unavailable"}')
    def do_POST(self):
        if not self.allowed() or self.headers.get('Content-Type')!='application/json':self.reply(403,b'{"ok":false}');return
        if self.path not in ('/view/start','/view/stop') or self.headers.get('Content-Length')!='2':self.reply(400,b'{"ok":false}');return
        if self.rfile.read(2)!=b'{}':self.reply(400,b'{"ok":false}');return
        result=self.server.viewer.start() if self.path=='/view/start' else self.server.viewer.stop()
        self.reply(200,json.dumps(result).encode())

class Server(ThreadingHTTPServer):
    daemon_threads=True
    request_queue_size=4
    def __init__(self,*args,**kwargs):
        self.slots=threading.BoundedSemaphore(4);super().__init__(*args,**kwargs)
    def process_request(self,request,address):
        if not self.slots.acquire(blocking=False):self.shutdown_request(request);return
        try:super().process_request(request,address)
        except Exception:self.slots.release();raise
    def process_request_thread(self,request,address):
        try:super().process_request_thread(request,address)
        finally:self.slots.release()
    def service_actions(self):self.viewer.expire()
    def get_request(self):
        connection,address=super().get_request();connection.settimeout(10);return connection,address

def main():
    os.umask(0o077)
    server=Server(('127.0.0.1',15102),Handler);server.viewer=Viewer()
    try:server.serve_forever(poll_interval=.5)
    finally:server.viewer.stop();server.server_close()

if __name__=='__main__':main()
