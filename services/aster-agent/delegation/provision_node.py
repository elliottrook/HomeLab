"""Approved-only source-local endpoints for owned controller pipes.

No command executes by default. Secret frames must never be run as ordinary
agent tool output; only the private controller consumes this protocol.
"""
import json
import os
from pathlib import Path
import select
import ssl
import stat
import sys
import time
import urllib.error
import urllib.request

PREFIX='ASTER_PROVISION='
ADMIN=Path('/run/aster-worker-provision/admin.token')
FRAME_TIMEOUT=120
WRITE_TIMEOUT=15
_buffer=b''


def receive():
    global _buffer
    deadline=time.monotonic()+FRAME_TIMEOUT
    while b'\n' not in _buffer:
        remaining=deadline-time.monotonic()
        if remaining<=0 or not select.select([sys.stdin],[],[],remaining)[0]:
            raise ValueError('Controller unavailable')
        chunk=os.read(sys.stdin.fileno(),65536)
        if not chunk: raise ValueError('Controller disconnected')
        _buffer+=chunk
        if len(_buffer)>131072: raise ValueError('Invalid private frame')
    raw,_buffer=_buffer.split(b'\n',1)
    if not raw or len(raw)+1>65536: raise ValueError('Invalid private frame')
    value=json.loads(raw)
    if not isinstance(value,dict): raise ValueError('Invalid private frame')
    return value


def send(kind,value):
    data=(PREFIX+json.dumps({'kind':kind,'value':value},separators=(',',':'))+'\n').encode()
    if len(data)>65536: raise ValueError('Invalid private frame')
    fd=sys.stdout.fileno();was_blocking=os.get_blocking(fd)
    os.set_blocking(fd,False)
    try:
        deadline=time.monotonic()+WRITE_TIMEOUT
        while data:
            remaining=deadline-time.monotonic()
            if remaining<=0 or not select.select([],[fd],[],remaining)[1]:
                raise ValueError('Controller unavailable')
            try: data=data[os.write(fd,data):]
            except BlockingIOError: pass
    finally:
        os.set_blocking(fd,was_blocking)


def acknowledged(kind,value):
    send(kind,value)
    if receive()!={'accepted':True}: raise ValueError('Delivery unconfirmed')
    return True


def identity():
    import identity_provision as module
    try:
        request=receive()
        if set(request)!={'approved_sha256'}: raise ValueError('Invalid request')
        result=module.provision(lambda packet:acknowledged('identity_credentials',packet),
            approved_sha256=request['approved_sha256'],
            observe=lambda stage,record:acknowledged('identity_stage',{'stage':stage,'record':record}))
        send('identity_done',result)
    except Exception:
        send('error',{'code':'identity_incomplete'})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None


def vault():
    import vault_provision as module
    token=None;inode=None
    try:
        request=receive()
        if set(request)!={'approved_sha256','credentials'}: raise ValueError('Invalid request')
        if request['approved_sha256']!=module.fingerprint(): raise ValueError('Fingerprint mismatch')
        context=ssl.create_default_context(cafile='/opt/openbao/tls/tls.crt')
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect(),
                                        urllib.request.HTTPSHandler(context=context))
        # Exact reviewed patch: 2.6.3 cannot enforce the assumed SecretID expiry.
        # Check before opening administrative custody or provisioning anything.
        with opener.open('https://127.0.0.1:8200/v1/sys/health',timeout=10) as health:
            body=health.read(65537)
            if len(body)>65536 or json.loads(body).get('version')!='2.6.4':
                raise ValueError('Reviewed vault patch required')
        fd=os.open(ADMIN,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            info=os.fstat(fd);inode=(info.st_dev,info.st_ino)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_mode&0o077
                    or info.st_nlink!=1 or not 1<=info.st_size<=16384):
                raise ValueError('Unsafe temporary admin custody')
            token=os.read(fd,16385).decode().strip()
            if not token or any(c.isspace() for c in token): raise ValueError('Invalid token')
        finally: os.close(fd)
        def api(method,path,payload):
            req=urllib.request.Request('https://127.0.0.1:8200/v1/'+path,
                data=None if payload is None else json.dumps(payload).encode(),method=method,
                headers={'X-Vault-Token':token,'Content-Type':'application/json'})
            try:
                with opener.open(req,timeout=10) as response:
                    raw=response.read(65537)
                    if len(raw)>65536: raise ValueError('Oversized vault response')
                    return response.status,json.loads(raw) if raw else {}
            except urllib.error.HTTPError as error:
                status=error.code;error.close();return status,{}
        try:
            result=module.provision(api,lambda packet:acknowledged('role_credentials',packet),
                request['credentials'],approved_sha256=request['approved_sha256'],
                observe=lambda stage:acknowledged('vault_stage',{'stage':stage}))
        finally:
            status,_=api('POST','auth/token/revoke-self',{})
            if status not in (200,204): raise ValueError('Admin revocation unconfirmed')
            now=ADMIN.lstat()
            if (now.st_dev,now.st_ino)!=inode: raise ValueError('Admin file changed')
            ADMIN.unlink()
            acknowledged('admin_revoked',{'confirmed':True})
        send('vault_done',result)
    except Exception:
        send('error',{'code':'vault_incomplete'})


def gateway():
    import credential_delivery
    try:
        packet=receive()
        if set(packet)!={'role_id','secret_id','secret_id_accessor'}: raise ValueError('Invalid packet')
        result=credential_delivery.install(packet,enabled=True)
        send('gateway_done',{'confirmed':result is True})
    except Exception:
        send('error',{'code':'gateway_delivery_incomplete'})
