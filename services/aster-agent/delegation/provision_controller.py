"""Owned-pipe provisioning controller candidate. Default is public metadata.

The separate approved staging/human ceremony must already be complete. This
controller never opens recovery shares or receives the vault administrator token.
Identity remains inactive; no service restart, model call or activation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import shlex
import subprocess
import time

from provision_journal import Journal
import identity_provision
import vault_provision

ROOT=Path(__file__).parent
STAGE='/var/tmp/aster-worker-provision-20261006'
SOURCES=('provision_controller.py','provision_node.py','provision_journal.py','admin_contract.py',
         'identity_provision.py','vault_provision.py','credential_delivery.py','credentials.py',
         'deploy/introspection-read.hcl','deploy/introspection-role.json',
         'deploy/InstallWorkerCredential.swift')
PREFIX=b'ASTER_PROVISION='
VAULT_STAGES=tuple(name+':'+state for name in (
    'policy','role','aster-worker-introspection','aster-codex-worker','secret-id','delivery')
    for state in ('attempted','confirmed'))


def manifest():
    return {'sources':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES},
            'identity_sha256':identity_provision.fingerprint(),
            'vault_sha256':vault_provision.fingerprint(),
            'targets':[104,106,117],'stage':STAGE,'activation':False,'model_calls':0}


def fingerprint():
    return hashlib.sha256(json.dumps(manifest(),sort_keys=True).encode()).hexdigest()


class Pipe:
    def __init__(self,command):
        self.process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL)
        self.buffer=b'';self.skipped=0

    def send(self,value):
        data=json.dumps(value,separators=(',',':')).encode()+b'\n'
        if len(data)>65536: raise ValueError('Private frame too large')
        fd=self.process.stdin.fileno();os.set_blocking(fd,False)
        deadline=time.monotonic()+15
        while data:
            remaining=deadline-time.monotonic()
            if remaining<=0 or not select.select([],[fd],[],remaining)[1]:
                raise ValueError('Private write deadline')
            try: data=data[os.write(fd,data):]
            except BlockingIOError: pass

    def receive(self):
        deadline=time.monotonic()+120
        while True:
            if b'\n' in self.buffer:
                line,self.buffer=self.buffer.split(b'\n',1)
                if not line.startswith(PREFIX):
                    self.skipped+=len(line)+1
                    if self.skipped>65536: raise ValueError('Unexpected startup output')
                    continue
                value=json.loads(line[len(PREFIX):])
                if not isinstance(value,dict) or set(value)!={'kind','value'}:
                    raise ValueError('Invalid private response')
                return value['kind'],value['value']
            remaining=deadline-time.monotonic()
            if remaining<=0 or not select.select([self.process.stdout],[],[],remaining)[0]:
                raise ValueError('Private read deadline')
            chunk=os.read(self.process.stdout.fileno(),65536)
            if not chunk: raise ValueError('Private peer disconnected')
            self.buffer+=chunk
            if len(self.buffer)>131072: raise ValueError('Private response too large')

    def close(self):
        self.process.stdin.close()
        try: self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try: self.process.wait(timeout=5)
            except subprocess.TimeoutExpired: self.process.kill();self.process.wait()
        self.process.stdout.close()


def remote(mode):
    hashes=manifest()['sources']
    code=('import sys,pathlib,hashlib;root=pathlib.Path('+repr(STAGE)+');'
          'expected='+repr(hashes)+';'
          'assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in expected.items());'
          'sys.path.insert(0,str(root));import provision_node;provision_node.'+mode+'()')
    if mode=='identity':
        command='pct exec 106 -- docker exec -i authentik-server-1 ak shell -c '+shlex.quote(code)
    elif mode in ('vault','gateway'):
        guest=117 if mode=='vault' else 104
        command='pct exec '+str(guest)+' -- python3 -B -u -c '+shlex.quote(code)
    else: raise ValueError('Unsupported target')
    return Pipe(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','proxmox',command])


def keychain(password,binary):
    from credentials import KEYCHAIN_SERVICE,KEYCHAIN_ACCOUNT
    result=subprocess.run([str(binary),'--install'],input=password.encode(),
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=30,check=True)
    if json.loads(result.stdout)!={'created':True,'overwritten':False,'roundtrip_verified':False}:
        raise ValueError('Keychain installation unconfirmed')
    result=subprocess.run(['/usr/bin/security','find-generic-password','-s',KEYCHAIN_SERVICE,
        '-a',KEYCHAIN_ACCOUNT,'-w'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,timeout=15,check=True)
    if result.stdout.removesuffix(b'\n')!=password.encode():
        raise ValueError('Keychain receipt unconfirmed')


def run(directory,*,approved_sha256=None,peer_factory=remote,keychain_sink=keychain):
    if approved_sha256!=fingerprint(): raise ValueError('Exact controller approval required')
    journal=Journal(directory)
    peers=[]
    try:
        binary=Path(directory)/'InstallWorkerCredential'
        subprocess.run(['/usr/bin/xcrun','swiftc',str(ROOT/'deploy/InstallWorkerCredential.swift'),
            '-o',str(binary)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,check=True)
        identity=peer_factory('identity');peers.append(identity)
        identity.send({'approved_sha256':identity_provision.fingerprint()})
        identity_stages=[];handoff=False
        while True:
            kind,value=identity.receive()
            if kind=='identity_stage':
                expected=('identity:attempted','identity:confirmed')
                if len(identity_stages)>=2 or value['stage']!=expected[len(identity_stages)]:
                    raise ValueError('Identity stage ordering invalid')
                journal.note(value['stage'],value['record']);identity.send({'accepted':True})
                identity_stages.append(value['stage'])
            elif kind=='identity_credentials' and len(identity_stages)==2 and not handoff:
                handoff=True
                if not isinstance(value,dict) or set(value)!={'client_secret','app_password'}:
                    raise ValueError('Invalid identity frame')
                vault=peer_factory('vault');peers.append(vault)
                vault.send({'approved_sha256':vault_provision.fingerprint(),'credentials':value})
                delivered=False;revoked=False;vault_stages=[]
                while True:
                    vkind,vvalue=vault.receive()
                    if vkind=='vault_stage':
                        if (len(vault_stages)>=len(VAULT_STAGES)
                                or vvalue!={'stage':VAULT_STAGES[len(vault_stages)]}
                                or (vvalue['stage']=='delivery:confirmed' and not delivered)):
                            raise ValueError('Vault stage ordering invalid')
                        journal.note('vault:'+vvalue['stage']);vault.send({'accepted':True})
                        vault_stages.append(vvalue['stage'])
                    elif vkind=='role_credentials' and not delivered and tuple(vault_stages)==VAULT_STAGES[:-1]:
                        journal.note('gateway:attempted')
                        gateway=peer_factory('gateway');peers.append(gateway);gateway.send(vvalue)
                        if gateway.receive()!=('gateway_done',{'confirmed':True}):
                            raise ValueError('Gateway receipt unconfirmed')
                        journal.note('gateway:confirmed')
                        journal.note('keychain:attempted')
                        keychain_sink(value['app_password'],binary)
                        journal.note('keychain:confirmed');delivered=True
                        vault.send({'accepted':True})
                    elif (vkind=='admin_revoked' and vvalue=={'confirmed':True}
                          and not revoked and delivered and tuple(vault_stages)==VAULT_STAGES):
                        journal.note('admin:revoked');revoked=True;vault.send({'accepted':True})
                    elif vkind=='vault_done' and delivered and revoked and vvalue.get('complete') is True:
                        break
                    else: raise ValueError('Vault provisioning unconfirmed')
                identity.send({'accepted':True})
            elif kind=='identity_done' and handoff and value.get('activated') is False and value.get('delivery_confirmed') is True:
                journal.note('complete')
                return {'complete':True,'worker_active':False,'delegation_enabled':False,'model_calls':0}
            else: raise ValueError('Identity provisioning unconfirmed')
    except Exception:
        journal.note('incomplete')
        raise RuntimeError('Provisioning incomplete; inspect stage journal and reconcile without retry') from None
    finally:
        for peer in reversed(peers): peer.close()
        journal.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    parser.add_argument('--approved-sha256');parser.add_argument('--journal',type=Path)
    args=parser.parse_args()
    if not args.run: print(json.dumps({'manifest':manifest(),'sha256':fingerprint(),'applied':False},indent=2))
    elif args.journal is None: raise SystemExit('Fresh private journal required')
    else:
        try: print(json.dumps(run(args.journal,approved_sha256=args.approved_sha256)))
        except Exception: raise SystemExit('Provisioning incomplete; reconcile without retry') from None
