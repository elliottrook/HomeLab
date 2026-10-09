"""Separate approval required: lost-response and exact-target recovery fixture."""
import argparse
import hashlib
import json
from pathlib import Path

import human_ceremony
import human_root_recovery
import isolated_ceremony_rehearsal as base

ROOT=Path(__file__).parent
SOURCES=tuple(n for n in base.SOURCES if n!='deploy/aster-ceremony-isolated.service')+(
    'human_root_recovery.py','isolated_root_recovery_rehearsal.py',
    'deploy/aster-root-recovery-isolated.service')


def manifest():
    return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES}


def check(api,supervisor,role,shares):
    def generate(consume,drop_final=False):
        status,body=api(supervisor,'POST','auth/approle/role/human-root-ceremony/secret-id',{})
        assert status==200
        values=iter([role,body['data']['secret_id'],*shares[:2]])
        def transport(token,method,path,payload=None):
            status,body=api(token,method,path,payload)
            if drop_final and path==human_ceremony.UPDATE and body.get('data',{}).get('complete'):
                # Server has committed a real fixture root; client loses receipt.
                raise TimeoutError('Fictional lost final response')
            return status,body
        return human_ceremony.ceremony(transport,lambda _:next(values),consume)

    baseline=set(human_root_recovery.accessors(api,supervisor))
    try: generate(lambda _:False,drop_final=True)
    except (TimeoutError,RuntimeError): pass
    else: raise AssertionError('Fault did not occur')
    # Fixture supervisor knows its isolated inventory before the fault. This is
    # a test oracle, NOT an ownership inference offered in production recovery.
    delta=set(human_root_recovery.accessors(api,supervisor))-baseline
    lost=[a for a in delta if human_root_recovery.generated_root(
        human_root_recovery.lookup(api,supervisor,a))]
    assert len(lost)==1
    target=lost[0]
    saved=[]
    def reject(root):
        saved.append(root)
        return human_root_recovery.recover(api,root,lambda _:'REVOKE absent')
    try: generate(reject)
    except ValueError: pass
    else: raise AssertionError('Invalid selection accepted')
    assert len(saved)==1 and api(saved[0],'GET','auth/token/lookup-self')[0]==403
    assert target in human_root_recovery.accessors(api,supervisor)
    def accept(root):
        saved.append(root)
        return human_root_recovery.recover(api,root,lambda _:'REVOKE '+target)
    assert generate(accept)['target_revoked'] is True
    assert len(saved)==2 and api(saved[1],'GET','auth/token/lookup-self')[0]==403
    assert target not in human_root_recovery.accessors(api,supervisor)
    assert api(supervisor,'GET','auth/token/lookup-self')[0]==200


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if not args.run: print(json.dumps({'applied':False,'files':manifest()}))
    else:
        try:
            result=base.execute(recovery_check=check)
            if result['passed']:
                result.update({'lost_final_response_recovered':True,
                               'wrong_target_rejected':True,'unrelated_root_preserved':True})
        except Exception: result={'passed':False,'failed_stage':'isolation-preflight'}
        print(json.dumps(result));raise SystemExit(0 if result['passed'] else 1)
