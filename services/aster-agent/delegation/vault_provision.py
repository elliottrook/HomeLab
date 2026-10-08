"""Source-local vault provisioning candidate. Default emits a public manifest.

No CLI apply path: the reviewed source-local transport must supply API and
delivery callbacks. Never paste credentials into an agent command. An approved
fingerprint binds code/policy/role, not human authority by itself.
"""
import hashlib
import json
from pathlib import Path
import admin_contract

ROOT = Path(__file__).parent
POLICY_PATH = 'sys/policies/acl/aster-worker-introspection-read'
ROLE_PATH = 'auth/approle/role/aster-worker-introspection'
SECRET_NAMES = ('aster-worker-introspection', 'aster-codex-worker')


def manifest():
    files = ('vault_provision.py', 'admin_contract.py', 'deploy/introspection-read.hcl',
             'deploy/introspection-role.json')
    return {
        'source_hashes': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files},
        'policy': POLICY_PATH, 'role': ROLE_PATH,
        'secrets': list(SECRET_NAMES), 'overwrite': False,
        'secret_id_ttl_seconds': 86400, 'model_calls': 0,
        'automatic_retry': False, 'deployment': False,
    }


def fingerprint():
    return hashlib.sha256(json.dumps(manifest(),sort_keys=True,separators=(',',':')).encode()).hexdigest()


class ProvisioningIncomplete(Exception):
    def __init__(self, stages):
        self.stages = tuple(stages)
        super().__init__('Provisioning incomplete; reconcile recorded stages before retry')


def provision(api, deliver, secrets, *, approved_sha256=None, observe=None):
    """api(method,path,payload) returns (status, dict), never logs bodies.

    deliver(packet) must return literal True after protected destination receipt.
    The source-local controller owns temporary admin-token self-revocation and
    calls this only in an exclusive human-approved administration window.
    """
    if approved_sha256 != fingerprint():
        raise ValueError('Exact provisioning fingerprint required')
    if (not isinstance(secrets,dict) or set(secrets) != {'client_secret','app_password'}
            or any(not isinstance(v,str) or not 1<=len(v)<=16384 or
                   any(c.isspace() for c in v) for v in secrets.values())):
        raise ValueError('Invalid source-local provisioning input')
    stages=[]

    def note(stage):
        stages.append(stage)
        if observe is not None: observe(stage)

    def absent(path):
        status,_=api('GET',path,None)
        if status!=404:
            raise ValueError('Existing or unverifiable object')

    def write(path,value,name):
        # Record intent before sending: a lost response may follow a real write.
        note(name+':attempted')
        status,result=api('POST',path,value)
        if status not in (200,204): raise ValueError('Write unconfirmed')
        note(name+':confirmed')
        return result

    try:
        # Fixed config is human-bootstrapped. Ordinary provisioning has no policy
        # or role write permissions; stages below record verification only.
        note('policy:attempted')
        status,value=api('GET',POLICY_PATH,None)
        if status!=200 or value.get('data',{}).get('policy')!=(ROOT/'deploy/introspection-read.hcl').read_text():
            raise ValueError('Fixed policy mismatch')
        note('policy:confirmed');note('role:attempted')
        status,value=api('GET',ROLE_PATH,None)
        if status!=200: raise ValueError('Fixed role unavailable')
        admin_contract.verify_role(value.get('data'))
        note('role:confirmed')
        for name in SECRET_NAMES: absent('secret/metadata/ai-pam/'+name)
        for name,key in zip(SECRET_NAMES,('client_secret','app_password')):
            result=write('secret/data/ai-pam/'+name,
                         {'options':{'cas':0},'data':{key:secrets[key]}},name)
            if result.get('data',{}).get('version') != 1:
                raise ValueError('Unexpected secret version')
            status,value=api('GET','secret/data/ai-pam/'+name,None)
            if status!=200 or value.get('data',{}).get('data') != {key:secrets[key]}:
                raise ValueError('Custody round trip failed')
        status,role_id=api('GET',ROLE_PATH+'/role-id',None)
        if status!=200: raise ValueError('Role identity unavailable')
        result=write(ROLE_PATH+'/secret-id',{},'secret-id')
        packet={'role_id':role_id.get('data',{}).get('role_id'),
                'secret_id':result.get('data',{}).get('secret_id'),
                'secret_id_accessor':result.get('data',{}).get('secret_id_accessor')}
        if any(not isinstance(v,str) or not 1<=len(v)<=16384 for v in packet.values()):
            raise ValueError('Invalid role credential response')
        note('delivery:attempted')
        if deliver(packet) is not True: raise ValueError('Protected delivery unconfirmed')
        note('delivery:confirmed')
        return {'complete':True,'stages':stages,'credentials_printed':False}
    except Exception:
        # No broad deletion on uncertainty; retain an explicit recovery boundary.
        raise ProvisioningIncomplete(stages) from None


if __name__=='__main__':
    print(json.dumps({'manifest':manifest(),'sha256':fingerprint(),'applied':False},indent=2))
