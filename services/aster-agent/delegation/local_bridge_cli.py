"""Explicit one-shot native bridge; never a background service.

Preparation performs metadata checks only. A connected run requires a separate
reviewed manifest, exact consent and one private stdin request. No prompt is
placed in argv, environment, a manifest or the durable dispatch journal.
The installed fixed-fixture pilot has consumed its one approved turn. Further
connected evaluation remains subject to a separate reviewed gate.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import sys
import tempfile
import time
import uuid

from isolation_probe import ConfigClient, disable_mcp_options, summarize
from local_turn import run_local_turn
from pilot import fingerprint, initialize, manifest, options
from pipe_worker import PipeAgent
from runtime import open_runtime


class RecoveryConfigClient(ConfigClient):
    """Read an already recorded turn; never create a thread or start a turn."""
    methods = ConfigClient.methods | {'thread/read'}


def recorded_row(directory, request_id):
    """Inspect only this owner's metadata; never start Codex or create state."""
    if (not isinstance(request_id, str) or
            not re.fullmatch(r'request-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',request_id)):
        raise ValueError('Invalid recorded request ID')
    path=Path(directory)
    if not path.is_absolute() or path.resolve()!=path:
        raise ValueError('Invalid private state path')
    for candidate,kind in ((path,stat.S_ISDIR),(path/'jobs.sqlite',stat.S_ISREG)):
        info=candidate.lstat()
        if not kind(info.st_mode) or info.st_uid!=os.geteuid() or info.st_mode & 0o077:
            raise ValueError('Private journal unavailable')
    db=sqlite3.connect((path/'jobs.sqlite').as_uri()+'?mode=ro',uri=True)
    try:
        row=db.execute('SELECT state,thread_id,turn_id FROM jobs WHERE job_id=? AND owner=?',
                       (request_id,'uid:'+str(os.getuid()))).fetchone()
    finally:
        db.close()
    return row


def recorded_status(directory, request_id):
    row=recorded_row(directory,request_id)
    return {'id':request_id,'recorded':row is not None,
            'state':row[0] if row else 'unrecorded',
            'turn_recorded':bool(row and row[2])}


def recover_snapshot(snapshot, thread_id, turn_id):
    """Release only one completed final answer from the bound full snapshot."""
    if not isinstance(snapshot,dict):
        raise ValueError('Recovery snapshot unavailable')
    thread=snapshot.get('thread')
    if not isinstance(thread,dict) or thread.get('id')!=thread_id:
        raise ValueError('Recovery thread mismatch')
    turns=thread.get('turns')
    if not isinstance(turns,list):
        raise ValueError('Recovery turns unavailable')
    matches=[turn for turn in turns if isinstance(turn,dict) and turn.get('id')==turn_id]
    if len(matches)!=1 or matches[0].get('status')!='completed' or matches[0].get('itemsView')!='full':
        raise ValueError('Recovery turn incomplete')
    items=matches[0].get('items')
    if not isinstance(items,list) or any(not isinstance(item,dict) or
           item.get('type') not in {'userMessage','agentMessage','reasoning'} for item in items):
        raise ValueError('Recovery contained unsupported items')
    answers=[item.get('text') for item in items if item.get('type')=='agentMessage'
             and item.get('phase')=='final_answer']
    if len(answers)!=1 or not isinstance(answers[0],str) or not 1<=len(answers[0].encode())<=65536:
        raise ValueError('Recovery answer unavailable')
    return answers[0]


def recovery_preflight(config, account):
    """Read-only historical access does not depend on today's model catalogue."""
    check=summarize(config)
    if (check['disabled_flags_unconfirmed'] or check['enabled_mcp_count'] or
            check['inherited_instruction_present'] or not check['read_only_requested'] or
            not check['web_search_disabled'] or
            (account.get('account') or {}).get('type')!='chatgpt' or
            config.get('model_provider')!='openai' or
            (config.get('model_providers') or {}).get('openai')):
        raise ValueError('Recovery account or isolation changed')
    for key,allowed in {'openai_base_url':{'https://api.openai.com/v1'},
                        'chatgpt_base_url':{'https://chatgpt.com/backend-api',
                                            'https://chatgpt.com/backend-api/codex'}}.items():
        value=config.get(key)
        if value and value.rstrip('/') not in allowed:
            raise ValueError('Recovery endpoint changed')


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
    mode.add_argument('--status',action='store_true')
    mode.add_argument('--recover',action='store_true')
    mode.add_argument('--reconcile',action='store_true')
    mode.add_argument('--recover-check',action='store_true')
    parser.add_argument('--approved-sha256')
    parser.add_argument('--state-dir',type=Path)
    parser.add_argument('--request-id')
    args=parser.parse_args(argv)
    if args.status:
        if not args.state_dir or not args.request_id or args.approved_sha256:
            raise SystemExit('Private recorded status parameters required')
        try:
            print(json.dumps(recorded_status(args.state_dir,args.request_id),sort_keys=True))
        except Exception:
            raise SystemExit('Local status unavailable') from None
        return
    if args.request_id and not (args.recover or args.reconcile):
        raise SystemExit('Recorded request ID is only valid for status or recovery')
    if not (args.prepare or args.run or args.recover or args.reconcile or args.recover_check):
        print(json.dumps({'enabled':False,'inference':False}))
        return
    if args.run and (not args.approved_sha256 or not args.state_dir or
                     not args.state_dir.is_absolute() or
                     args.state_dir.resolve()!=args.state_dir):
        raise SystemExit('Reviewed manifest and private absolute state directory required')
    recovery_mode=args.recover or args.reconcile
    if recovery_mode and (args.approved_sha256 or not args.state_dir or
                          not args.state_dir.is_absolute() or
                          args.state_dir.resolve()!=args.state_dir):
        raise SystemExit('Private recovery state directory required')
    if args.recover_check and (args.approved_sha256 or args.state_dir):
        raise SystemExit('Recovery preflight takes no request or state path')
    row=None
    if recovery_mode:
        row=recorded_row(args.state_dir,args.request_id)
        eligible={'completed'} if args.recover else {'running','unknown','cancel_requested'}
        if not row or row[0] not in eligible or not row[1] or not row[2]:
            raise SystemExit('Original completed turn unavailable')
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
        client_type=RecoveryConfigClient if recovery_mode else ConfigClient
        client=client_type(executable,options=opts,cwd=cwd)
        try:
            initialize(client)
            config=client.call('config/read',{'includeLayers':False,'cwd':cwd})['config']
        finally:
            client.close()
        opts+=disable_mcp_options(config)
        client=client_type(executable,options=opts,cwd=cwd)
        try:
            initialize(client)
            if recovery_mode or args.recover_check:
                recovery_preflight(client.call('config/read',{'includeLayers':False,'cwd':cwd})['config'],
                                   client.call('account/read',{'refreshToken':False}))
                if args.recover_check:
                    print(json.dumps({'recovery_ready':True,'inference':False},sort_keys=True))
                    return
                snapshot=client.call('thread/read',{'threadId':row[1],'includeTurns':True})
                answer=recover_snapshot(snapshot,row[1],row[2])
                if args.reconcile:
                    runtime=open_runtime(args.state_dir,enabled=True)
                    try:
                        expected=('unknown',row[1],row[2])
                        if runtime.store.inspect_owned(args.request_id,
                                'uid:'+str(os.getuid()))!=expected:
                            raise ValueError('Recorded turn changed during reconciliation')
                        runtime.store.finish(args.request_id,row[1],row[2],'completed')
                    finally:
                        runtime.close()
                print(json.dumps({'id':args.request_id,'state':'completed','answer':answer,
                                  'automatic_retry':False,'inference':False},ensure_ascii=False))
                return
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
                started=time.monotonic()
                result=run_local_turn(agent,runtime.store,job_id,
                    'uid:'+str(os.getuid()),text,prepared['model'])
                elapsed=round(time.monotonic()-started,3)
                # The answer is volatile and exits only through the caller's
                # private stdout pipe. Never put it in logs or the journal.
                print(json.dumps({'id':job_id,**result,
                                  'elapsed_seconds':elapsed},ensure_ascii=False))
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
