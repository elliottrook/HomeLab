"""Explicitly enabled credential-path check, no job admission or inference.

Uses the fixed private custody adapter; emits only status codes and booleans.
The valid credential is never returned to the caller or written to a file.
"""
import argparse
import json
import httpx
from credentials import WorkerToken

URL='https://aster.elliottrook.com/v1/delegation/worker/jobs/orion-preflight-unassigned/offer'


def check(*,enabled=False,token_source=None,transport=None):
    if enabled is not True:
        raise ValueError('Separate pilot authorization required')
    token_source=token_source or WorkerToken(enabled=True)
    with httpx.Client(timeout=10,follow_redirects=False,trust_env=False,transport=transport) as client:
        missing=client.post(URL).status_code
        malformed=client.post(URL,headers={'Authorization':'Bearer invalid-pilot-fixture'}).status_code
        if missing!=401 or malformed!=401:
            raise ValueError('Unauthenticated access did not fail closed')
        token=token_source()
        response=client.post(URL,headers={'Authorization':'Bearer '+token})
        if response.status_code!=404 or response.json()!={'detail':'Job not found'}:
            raise ValueError('Authenticated gateway path unconfirmed')
    return {'credential_path_confirmed':True,'missing_auth_status':missing,
            'malformed_auth_status':malformed,'unassigned_job_status':404,
            'jobs_admitted':0,'model_calls':0,'credentials_printed':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    try:
        print(json.dumps(check(enabled=True) if args.run else {'enabled':False,'model_calls':0}))
    except Exception:
        raise SystemExit('Credential path unconfirmed; no job admitted') from None
