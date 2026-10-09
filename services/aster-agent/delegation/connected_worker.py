"""Operator-started single-assignment worker candidate; no automatic startup.

Default prints requirements only. --prepare reads installed Codex metadata but
does not access Keychain, contact Aster or infer. --run needs separate approval
of the exact prepared hash. Payload remains the fixed fictional Orion exercise.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from worker_session import WorkerSession
from credentials import CredentialUnavailable
from pilot_connection_check import check as connection_check
from handoff import WorkerInbox
from isolation_probe import ConfigClient, disable_mcp_options
from pilot import FIXTURE, fingerprint, initialize, manifest, options
from pipe_worker import PipeAgent
from runtime import open_runtime, private_file
from worker import run_one
from worker_client import WorkerClient


def connected_manifest(base, job_id):
    if not isinstance(job_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', job_id):
        raise ValueError('Invalid assigned job ID')
    scope = fingerprint({'scope':'fictional-orion-no-tools-v1','model':base['model']})
    return dict(base=base, job_id=job_id, gateway='aster-gateway',
        worker='aster-codex-worker-mac', scope_sha256=scope,
        request_sha256=hashlib.sha256(FIXTURE.encode()).hexdigest(),
        source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(Path(__file__).parent.glob('*.py'))},
        gateway_url='https://aster.elliottrook.com', maximum_model_turns=1,
        startup='manual', automatic_retry=False, tools=False,
        credential_bootstrap='supervised-once-90-seconds', token_renewal=False,
        api_fallback=False, request_content='fixed-fictional-orion')


async def execute(client, cwd, prepared, directory):
    # A fresh run directory is evidence, never a way to reset a gateway job ID.
    # The production gateway retains its ledger across runs and denies replay.
    if not directory.is_absolute() or directory.resolve() != directory:
        raise ValueError('Run directory must be absolute without symlinks')
    directory.mkdir(mode=0o700)
    for name in ('inbox.sqlite','manifest.json','result.json'):
        os.close(private_file(directory/name))
    (directory/'manifest.json').write_text(json.dumps(prepared,indent=2)+'\n')
    runtime = open_runtime(directory/'worker', enabled=True)
    inbox = None; agent = None
    session=WorkerSession(enabled=True)
    phase='session_bootstrap'
    try:
        await asyncio.to_thread(session.bootstrap)
        phase='gateway_credential_check'
        await asyncio.to_thread(connection_check,enabled=True,token_source=session)
        phase='assigned_worker_turn'
        inbox = WorkerInbox(directory/'inbox.sqlite', prepared['worker'],
            prepared['gateway'], [(prepared['scope_sha256'],prepared['base']['model'])])
        worker = WorkerClient(session, enabled=True)
        agent = PipeAgent(client,cwd,prepared['base']['model'],prepared['base']['reasoning_effort'])
        result = await run_one(worker,inbox,runtime.store,agent,
            prepared['job_id'],FIXTURE.encode(),enabled=True)
        # No answer, tokens, provider error text or hidden reasoning in stdout.
        summary = {key:result[key] for key in ('state','diagnostic') if key in result}
        summary.update(automatic_retry=False, job_id=prepared['job_id'])
        (directory/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
        return summary
    except Exception as exc:
        if isinstance(exc,CredentialUnavailable) and exc.stage:
            phase+=':'+exc.stage
        summary={'state':'unconfirmed','diagnostic':phase,'automatic_retry':False,
                 'job_id':prepared['job_id']}
        (directory/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
        return summary
    finally:
        session.close()
        if agent: agent.close()
        if inbox: inbox.close()
        runtime.close()


def main():
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--run',action='store_true')
    parser.add_argument('--job-id')
    parser.add_argument('--approved-sha256')
    parser.add_argument('--output-dir',type=Path)
    args=parser.parse_args()
    if not (args.prepare or args.run):
        print(json.dumps({'enabled':False,'startup':'manual','inference':False,
                          'requires':'provisioned identities and approved assigned job'}))
        return
    if not args.job_id or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',args.job_id):
        raise SystemExit('Exact assigned job ID required')
    if args.run and (not args.output_dir or not args.output_dir.is_absolute()
                     or not args.approved_sha256):
        raise SystemExit('Execution needs approved fingerprint and fresh absolute output directory')
    with tempfile.TemporaryDirectory(prefix='aster-connected-work-') as cwd:
        opts=options()
        client=ConfigClient(shutil.which('codex'),options=opts,cwd=cwd)
        try:
            initialize(client)
            cfg=client.call('config/read',{'includeLayers':False,'cwd':cwd})['config']
        finally: client.close()
        opts+=disable_mcp_options(cfg)
        client=ConfigClient(shutil.which('codex'),options=opts,cwd=cwd)
        try:
            initialize(client)
            cfg=client.call('config/read',{'includeLayers':False,'cwd':cwd})['config']
            prepared=connected_manifest(manifest(cfg,
                client.call('account/read',{'refreshToken':False}),
                client.call('model/list',{'limit':100,'includeHidden':False})),args.job_id)
            checksum=fingerprint(prepared)
            if args.prepare:
                print(json.dumps({'manifest':prepared,'manifest_sha256':checksum,'inference':False},indent=2))
            elif checksum != args.approved_sha256:
                raise SystemExit('Prepared scope changed; no inference')
            else:
                print(json.dumps(asyncio.run(execute(client,cwd,prepared,args.output_dir))))
        finally: client.close()


if __name__=='__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Worker incomplete; reconcile without reexecution') from None
