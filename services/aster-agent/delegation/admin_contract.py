"""Exact temporary provisioning authority; never accepts root or default policy."""
from pathlib import Path

POLICY='aster-worker-provision-once'
TTL=600
DISPLAY='aster-worker-provision-once'
ROOT=Path(__file__).parent


def policy():
    paths={
        'sys/policies/acl/aster-worker-introspection-read':['read'],
        'auth/approle/role/aster-worker-introspection':['read'],
        'auth/approle/role/aster-worker-introspection/role-id':['read'],
        'auth/approle/role/aster-worker-introspection/secret-id':['update'],
        'auth/token/lookup-self':['read'],
        'auth/token/revoke-self':['update'],
    }
    for name in ('aster-worker-introspection','aster-codex-worker'):
        paths['secret/metadata/ai-pam/'+name]=['read']
        paths['secret/data/ai-pam/'+name]=['read','create','update']
    import json
    return '\n'.join('path '+json.dumps(path)+' { capabilities = '+json.dumps(caps)+' }'
                     for path,caps in sorted(paths.items()))+'\n'


def role_request():
    import json
    return json.loads((ROOT/'deploy/introspection-role.json').read_text())


def verify_role(data):
    if not isinstance(data,dict): raise ValueError('Role unavailable')
    for key,value in role_request().items():
        if key.endswith('_ttl'):
            value={'24h':86400,'5m':300}[value]
        if type(data.get(key)) is not type(value) or data[key]!=value:
            raise ValueError('Role configuration mismatch')
    if data.get('token_period',0)!=0:
        raise ValueError('Periodic role not allowed')


def validate(data):
    if (not isinstance(data,dict) or data.get('policies')!=[POLICY]
        or data.get('identity_policies',[]) or data.get('renewable') is not False
        or data.get('orphan') is not True or data.get('explicit_max_ttl')!=TTL
        or type(data.get('ttl')) is not int or not 30<=data['ttl']<=TTL
        or data.get('display_name')!='token-'+DISPLAY
        or data.get('num_uses')!=0 or data.get('type')!='service'):
        raise ValueError('Temporary provisioning authority does not match contract')


def token_request():
    return {'policies':[POLICY],'no_default_policy':True,'no_parent':True,
            'ttl':'600s','explicit_max_ttl':'600s','renewable':False,
            'display_name':DISPLAY,'num_uses':0,'type':'service'}
