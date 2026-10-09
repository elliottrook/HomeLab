"""Operator-started, single-ticket read of an already completed Codex turn.

Preparation uses metadata only. Execution requires an exact manifest hash and a
fresh owner-issued ticket. There is no inference, list, retry or content log.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

from credentials import CredentialUnavailable
from isolation_probe import ConfigClient, disable_mcp_options
from pilot import fingerprint, initialize, manifest, options
from recovery_execution import ExactThreadReader, ReadOnlyDispatch, recover_once
from worker_client import WorkerClient
from worker_session import WorkerSession


class RecoveryClient(ConfigClient):
    methods = ConfigClient.methods | {'thread/read'}


def recovery_manifest(base, store_path, job_id, digest):
    if (not isinstance(job_id,str) or
            not re.fullmatch('[A-Za-z0-9_-]{1,128}',job_id) or
            not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest)):
        raise ValueError('Exact completed assignment required')
    store=ReadOnlyDispatch(store_path)
    try:
        row=store.inspect(job_id)
        if not row or row[0]!='completed' or not row[1] or not row[2]:
            raise ValueError('Completed local turn unavailable')
    finally:store.close()
    directory=Path(__file__).parent
    names=('supervised_answer_recovery.py','recovery_execution.py',
           'verified_recovery.py','recovery.py','worker_client.py',
           'worker_session.py','credentials.py','store.py')
    return {'base':base,'job_id':job_id,'result_sha256':digest,
            'dispatch_sha256':hashlib.sha256(Path(store_path).read_bytes()).hexdigest(),
            'source_hashes':{name:hashlib.sha256((directory/name).read_bytes()).hexdigest()
                             for name in names},
            'method':'thread/read','include_turns':True,'maximum_model_turns':0,
            'automatic_retry':False,'credential_bootstrap':'supervised-once'}


async def execute(client,prepared,store_path,ticket):
    """Any failed/uncertain response leaves the ticket for manual reconciliation."""
    if not re.fullmatch('[a-f0-9]{32}',ticket):
        raise ValueError('Exact recovery ticket required')
    store=ReadOnlyDispatch(store_path)
    session=WorkerSession(enabled=True)
    phase='bootstrap'
    try:
        await asyncio.to_thread(session.bootstrap)
        phase='original_turn_read'
        worker=WorkerClient(session,enabled=True)
        result=await recover_once(worker,ExactThreadReader(client),store,ticket,
                                  prepared['job_id'],prepared['result_sha256'])
        return result
    except Exception:
        # Never print provider content, credential errors or a recovered answer.
        return {'state':'unconfirmed','phase':phase,'job_id':prepared['job_id'],
                'automatic_retry':False}
    finally:
        session.close();store.close()


def main():
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--run',action='store_true')
    parser.add_argument('--store',type=Path)
    parser.add_argument('--job-id')
    parser.add_argument('--result-sha256')
    parser.add_argument('--ticket')
    parser.add_argument('--approved-sha256')
    args=parser.parse_args()
    if not (args.prepare or args.run):
        print(json.dumps({'enabled':False,'inference':False,'startup':'manual'}))
        return
    if not args.store or not args.job_id or not args.result_sha256:
        raise SystemExit('Exact local dispatch assignment required')
    if args.run and (not args.ticket or not args.approved_sha256):
        raise SystemExit('Run requires fresh ticket and approved manifest hash')
    executable=shutil.which('codex')
    if not executable:raise SystemExit('Codex unavailable')
    with tempfile.TemporaryDirectory(prefix='aster-answer-recovery-') as cwd:
        opts=options()
        client=ConfigClient(executable,options=opts,cwd=cwd)
        try:
            initialize(client)
            cfg=client.call('config/read',{'includeLayers':False,'cwd':cwd})['config']
        finally:client.close()
        opts+=disable_mcp_options(cfg)
        client=RecoveryClient(executable,options=opts,cwd=cwd)
        try:
            initialize(client)
            cfg=client.call('config/read',{'includeLayers':False,'cwd':cwd})['config']
            base=manifest(cfg,client.call('account/read',{'refreshToken':False}),
                          client.call('model/list',{'limit':100,'includeHidden':False}))
            base.pop('fixture',None)
            base['max_turns']=0
            prepared=recovery_manifest(base,args.store,args.job_id,args.result_sha256)
            checksum=fingerprint(prepared)
            if args.prepare:
                print(json.dumps({'manifest_sha256':checksum,'manifest':prepared,
                                  'inference':False},sort_keys=True))
            elif checksum!=args.approved_sha256:
                raise SystemExit('Recovery scope changed; no request sent')
            else:
                print(json.dumps(asyncio.run(execute(client,prepared,args.store,args.ticket)),
                                 sort_keys=True))
        finally:client.close()


if __name__=='__main__':
    try:main()
    except Exception:
        raise SystemExit('Recovery incomplete; reconcile without retry') from None
