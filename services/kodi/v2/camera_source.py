"""Frigate forced command: one reviewed JPEG only, never an arbitrary URL."""
import json
import math
import os
import signal
import sys
from urllib.request import build_opener,HTTPRedirectHandler

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*_args,**_kwargs):return None

def read_camera(opener=None):
    opener=opener or build_opener(NoRedirect())
    with opener.open('http://127.0.0.1:5000/api/stats',timeout=2) as reply:
        raw=reply.read(131073)
    if len(raw)>131072:raise ValueError('camera-stats-size')
    fps=json.loads(raw).get('cameras',{}).get('front_of_house',{}).get('camera_fps')
    if type(fps) not in (int,float) or not math.isfinite(fps) or not 0<fps<=120:raise ValueError('camera-not-live')
    with opener.open('http://127.0.0.1:5000/api/front_of_house/latest.jpg',timeout=3) as reply:
        if reply.status!=200 or reply.headers.get('Content-Type','').split(';')[0]!='image/jpeg':raise ValueError('camera-response')
        raw=reply.read(2097153)
    if not 4<len(raw)<=2097152 or not raw.startswith(b'\xff\xd8') or not raw.endswith(b'\xff\xd9'):raise ValueError('camera-image')
    return raw

def main():
    try:
        connection=os.environ.get('SSH_CONNECTION','').split()
        if len(sys.argv)!=1 or os.environ.get('SSH_ORIGINAL_COMMAND')!='aster-camera-front-v1' or len(connection)!=4 or connection[0] not in ('192.168.1.140','192.168.1.157') or connection[2]!='192.168.20.10' or connection[3]!='22':return 1
        signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('camera-timeout')));signal.alarm(6)
        raw=read_camera();sys.stdout.buffer.write(raw);sys.stdout.buffer.flush();return 0
    except Exception:return 1
    finally:signal.alarm(0)

if __name__=='__main__':raise SystemExit(main())
