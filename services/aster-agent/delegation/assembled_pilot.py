"""One fictional live Codex turn through the assembled worker; approval gated.

Gateway/owner HTTP identities are explicit local fixtures, not production auth.
Default prepares metadata only. The real Authentik/Mac path was tested separately.
No production route, credential, service, tool or paid API fallback is configured.
"""
import argparse
import asyncio
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException
from pilot import FIXTURE, options, initialize, manifest, fingerprint
from isolation_probe import ConfigClient, disable_mcp_options
from handoff import Gateway, WorkerInbox
from runtime import open_runtime, private_file
from worker_client import WorkerClient
from worker_router import worker_router, owner_result_router
from pipe_worker import PipeAgent
from worker import run_one


def assembled_manifest(base, *, cancel_after_ack=False):
    root = Path(__file__).parent
    # Include every local Python module to prevent an unreviewed adapter change.
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.glob('*.py'))}
    return dict(base=base, source_hashes=hashes, fixture=FIXTURE,
                gateway='in-process ASGI fixture', identity='fixture-only',
                maximum_model_turns=1, automatic_retry=False, tools=False,
                persistent_service=False, credential_changes=False,
                scope='fictional-orion-no-tools-v1',
                cancellation='first-running-receipt' if cancel_after_ack else 'not-requested')


async def execute(client, cwd, prepared, directory):
    directory.mkdir(mode=0o700)  # Exclusive, never overwrite a previous run.
    for name in ('gateway.sqlite','inbox.sqlite','manifest.json','result.json'):
        os.close(private_file(directory/name))
    (directory/'manifest.json').write_text(json.dumps(prepared,indent=2)+'\n')
    import time
    scope = fingerprint({'scope':prepared['scope'],'model':prepared['base']['model']})
    gateway = Gateway(directory/'gateway.sqlite','fixture-gateway')
    inbox = WorkerInbox(directory/'inbox.sqlite','fixture-worker','fixture-gateway',
                         [(scope,prepared['base']['model'])])
    runtime = None; agent = None
    try:
        runtime = open_runtime(directory/'worker',enabled=True)
        gateway.create('orion-assembled','fixture-owner','fixture-worker',
            hashlib.sha256(FIXTURE.encode()).hexdigest(),scope,
            prepared['base']['model'],int(time.time())+240)
        async def worker_identity(authorization: str=Header(default='')):
            if authorization != 'Bearer local-fixture':
                raise HTTPException(401,'Fixture identity required')
            return 'fixture-worker'
        async def owner_identity(): return 'fixture-owner'
        app = FastAPI()
        app.include_router(worker_router(gateway,worker_identity,enabled=True))
        app.include_router(owner_result_router(gateway,owner_identity,enabled=True))
        http = httpx.ASGITransport(app=app)
        class PilotWorkerClient(WorkerClient):
            stop_requested = False
            async def receipt(self, job_id, receipt):
                state = await super().receipt(job_id, receipt)
                if (prepared['cancellation'] == 'first-running-receipt' and
                        receipt['event'] == 'running' and not self.stop_requested):
                    self.stop_requested = True
                    async with httpx.AsyncClient(transport=http,base_url='https://aster.elliottrook.com') as owner:
                        stopped = await owner.post('/v1/companion/delegation/jobs/'+job_id+'/cancel')
                        stopped.raise_for_status()
                return state
        worker = PilotWorkerClient(lambda:'local-fixture',enabled=True,transport=http)
        agent = PipeAgent(client,cwd,prepared['base']['model'],prepared['base']['reasoning_effort'])
        started = time.monotonic()
        result = await run_one(worker,inbox,runtime.store,agent,'orion-assembled',FIXTURE.encode(),enabled=True)
        async with httpx.AsyncClient(transport=http,base_url='https://aster.elliottrook.com') as owner:
            response = await owner.get('/v1/companion/delegation/jobs/orion-assembled')
            response.raise_for_status()
            view = response.json()
        result.update(elapsed_seconds=round(time.monotonic()-started,3),owner_view=view,
                      production_deployment=False,model=prepared['base']['model'],
                      cancellation_requested=worker.stop_requested,
                      cancellation_confirmed=result['state']=='interrupted')
        (directory/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'state':result['state'],'answer_available':bool(view.get('reply')),
                          'usage_status':view['usage']['status'],'elapsed_seconds':result['elapsed_seconds'],
                          'cancellation_requested':worker.stop_requested,
                          'cancellation_confirmed':result['cancellation_confirmed'],
                          'production_deployment':False}))
    finally:
        if agent: agent.close()
        if runtime: runtime.close()
        inbox.close(); gateway.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--approved-sha256')
    parser.add_argument('--output-dir',type=Path)
    parser.add_argument('--cancel-after-ack',action='store_true')
    args = parser.parse_args()
    if args.run and (not args.output_dir or not args.output_dir.is_absolute() or not args.approved_sha256):
        raise SystemExit('Execution needs approved fingerprint and fresh absolute output directory')
    with tempfile.TemporaryDirectory(prefix='aster-assembled-work-') as cwd:
        opts = options()
        client = ConfigClient(shutil.which('codex'),options=opts,cwd=cwd)
        try:
            initialize(client)
            cfg = client.call('config/read',{'includeLayers':False,'cwd':cwd})['config']
        finally: client.close()
        opts += disable_mcp_options(cfg)
        client = ConfigClient(shutil.which('codex'),options=opts,cwd=cwd)
        try:
            initialize(client)
            cfg = client.call('config/read',{'includeLayers':False,'cwd':cwd})['config']
            base = manifest(cfg,client.call('account/read',{'refreshToken':False}),
                            client.call('model/list',{'limit':100,'includeHidden':False}))
            prepared = assembled_manifest(base,cancel_after_ack=args.cancel_after_ack)
            checksum = fingerprint(prepared)
            if not args.run:
                print(json.dumps({'manifest':prepared,'manifest_sha256':checksum,'inference':False},indent=2))
            elif checksum != args.approved_sha256:
                raise SystemExit('Prepared scope changed; no inference')
            else:
                asyncio.run(execute(client,cwd,prepared,args.output_dir))
        finally: client.close()


if __name__ == '__main__': main()
