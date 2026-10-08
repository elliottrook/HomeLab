"""Exact temporary provisioning authority; never accepts root or default policy."""
from pathlib import Path

POLICY='aster-worker-provision-once'
TTL=600
DISPLAY='aster-worker-provision-once'
ROOT=Path(__file__).parent


def policy():
    paths={
        'sys/policies/acl/aster-worker-introspection-read':['read','create','update'],
        'auth/approle/role/aster-worker-introspection':['read','create','update'],
        'auth/approle/role/aster-worker-introspection/role-id':['read'],
        'auth/approle/role/aster-worker-introspection/secret-id':['update'],
        'auth/token/lookup-self':['read'],
        'auth/token/revoke-self':['update'],
    }
    for name in ('aster-worker-introspection','aster-codex-worker'):
        paths['secret/metadata/ai-pam/'+name]=['read']
        paths['secret/data/ai-pam/'+name]=['read','create','update']
    import json
    role=json.loads((ROOT/'deploy/introspection-role.json').read_text())
    exact={
        'sys/policies/acl/aster-worker-introspection-read':{
            'policy':(ROOT/'deploy/introspection-read.hcl').read_text()},
        'auth/approle/role/aster-worker-introspection':role,
    }
    blocks=[]
    for path,caps in sorted(paths.items()):
        block='path '+json.dumps(path)+' { capabilities = '+json.dumps(caps)
        if path in exact:
            values=exact[path]
            # All fields required: omitted parameters must not silently select
            # less restrictive server defaults. No wildcard values permitted.
            block+='\n required_parameters = '+json.dumps(sorted(values))
            block+='\n allowed_parameters = {\n'
            for key,value in sorted(values.items()):
                block+=json.dumps(key)+' = '+json.dumps(value if isinstance(value,list) else [value])+'\n'
            block+='}'
        blocks.append(block+'\n}')
    return '\n'.join(blocks)+'\n'


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
