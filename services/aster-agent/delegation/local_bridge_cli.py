"""Disabled-by-default native bridge candidate; never a background service.

Preparation performs metadata checks only. A connected run requires a separate
reviewed manifest, exact consent and one private stdin request. No prompt is
placed in argv, environment, a manifest or the durable dispatch journal.
This candidate is not packaged in Companion or approved for live inference.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

from isolation_probe import ConfigClient, disable_mcp_options
from local_turn import run_local_turn
from pilot import fingerprint, initialize, manifest, options
from pipe_worker import PipeAgent
from runtime import open_runtime


def reviewed_request(raw):
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= 20000:
        raise ValueError('Reviewed request limit')
    value=json.loads(raw)
    if (not isinstance(value,dict) or
            set(value)!={'request_id','text','cloud_consent','local_only'} or
            value['cloud_consent'] is not True or value['local_only'] is not False or
            not isinstance(value['request_id'],str)):
        raise ValueError('Explicit reviewed consent required')
    identifier=str(uuid.UUID(value['request_id']))
    if identifier!=value['request_id']:
        raise ValueError('Canonical request ID required')
    text=value['text']
    if (not isinstance(text,str) or not text.strip() or '\x00' in text or
            len(text.encode('utf-8'))>16000):
        raise ValueError('Reviewed text limit')
    return 'request-'+identifier,text


def prepared_manifest(client,cwd):
    config=client.call('config/read',{'includeLayers':False,'cwd':cwd})['config']
    base=manifest(config,client.call('account/read',{'refreshToken':False}),
                  client.call('model/list',{'limit':100,'includeHidden':False}))
    if not base['codex_binary_sha256']:
        raise ValueError('Installed Codex binary could not be pinned')
    base.pop('fixture',None)
    base.update(request_mode='native-reviewed-stdin-one-turn',
                startup='explicit-one-shot', durable_content=False,
                local_bridge_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                local_turn_source_sha256=hashlib.sha256((Path(__file__).parent/'local_turn.py').read_bytes()).hexdigest(),
                pipe_worker_source_sha256=hashlib.sha256((Path(__file__).parent/'pipe_worker.py').read_bytes()).hexdigest())
    return base


def main(argv=None):
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--run',action='store_true')
    parser.add_argument('--approved-sha256')
    parser.add_argument('--state-dir',type=Path)
    args=parser.parse_args(argv)
    if not (args.prepare or args.run):
        print(json.dumps({'enabled':False,'inference':False}))
        return
    if args.run and (not args.approved_sha256 or not args.state_dir or
                     not args.state_dir.is_absolute() or
                     args.state_dir.resolve()!=args.state_dir):
        raise SystemExit('Reviewed manifest and private absolute state directory required')
    request=None
    if args.run:
        try:
            request=reviewed_request(sys.stdin.buffer.read(20001))
        except Exception:
            raise SystemExit('Reviewed request rejected before Codex startup') from None
    executable=shutil.which('codex')
    if not executable:
        raise SystemExit('Codex unavailable')
    with tempfile.TemporaryDirectory(prefix='aster-native-codex-') as cwd:
        opts=options()
        client=ConfigClient(executable,options=opts,cwd=cwd)
        try:
            initialize(client)
            config=client.call('config/read',{'includeLayers':False,'cwd':cwd})['config']
        finally:
            client.close()
        opts+=disable_mcp_options(config)
        client=ConfigClient(executable,options=opts,cwd=cwd)
        try:
            initialize(client)
            prepared=prepared_manifest(client,cwd)
            digest=fingerprint(prepared)
            if args.prepare:
                print(json.dumps({'manifest':prepared,'manifest_sha256':digest,
                                  'inference':False},sort_keys=True))
                return
            if digest!=args.approved_sha256:
                raise ValueError('Reviewed configuration changed')
            runtime=open_runtime(args.state_dir,enabled=True)
            agent=None
            try:
                agent=PipeAgent(client,cwd,prepared['model'],prepared['reasoning_effort'])
                job_id,text=request
                result=run_local_turn(agent,runtime.store,job_id,
                    'uid:'+str(os.getuid()),text,prepared['model'])
                # The answer is volatile and exits only through the caller's
                # private stdout pipe. Never put it in logs or the journal.
                print(json.dumps({'id':job_id,**result},ensure_ascii=False))
            finally:
                if agent:agent.close()
                runtime.close()
        except Exception:
            raise SystemExit('Local bridge incomplete; reconcile before retry') from None
        finally:
            client.close()


if __name__=='__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        raise SystemExit('Local bridge incomplete; reconcile before retry') from None
