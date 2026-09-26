"""Bounded fixed-command session; live spawn defaults to unconditional denial.

The injectable spawn seam is only for trusted local unit-test stubs. Command names
and argv come exclusively from the pinned reviewed catalogue, never a user path.
"""
import hashlib
import json
import os
import selectors
import signal
import subprocess
import time

from s0_lxc100_observe import command_catalog, require_pinned_catalog


def denied_spawn(*_, **__):
    raise PermissionError('real SSH spawn disabled pending final review')


class FixedSession:
    def __init__(self, operation, root_hash, *, spawn=denied_spawn, deadline=20, receipt=None):
        require_pinned_catalog(root_hash)
        catalog=command_catalog()
        if operation=='guarded-cleanup':
            from s0_owned_cleanup import argv
            catalog[operation]=argv(receipt)
        elif receipt is not None:raise ValueError('unexpected receipt')
        if type(operation) is not str or operation not in catalog:raise ValueError('unknown fixed operation')
        if type(deadline) not in (int,float) or not 0<deadline<=20:raise ValueError('deadline')
        self.operation=operation;self.argv=catalog[operation]
        self.argv_hash=hashlib.sha256(json.dumps(self.argv).encode()).hexdigest()
        self.started=time.monotonic();self.deadline=deadline;self.buffers={'stdout':bytearray(),'stderr':bytearray()}
        self.total=0;self.state='running';self.selector=selectors.DefaultSelector();self.closed=False
        try:
            self.process=spawn(self.argv,env={'LANG':'C','LC_ALL':'C'},stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,close_fds=True)
            for name,stream in [('stdout',self.process.stdout),('stderr',self.process.stderr)]:
                os.set_blocking(stream.fileno(),False);self.selector.register(stream,selectors.EVENT_READ,name)
        except BaseException:
            self.selector.close()
            if hasattr(self,'process'):self.close()
            raise

    def pump(self):
        if self.closed:raise ValueError('closed session')
        if time.monotonic()-self.started>=self.deadline:self.state='timeout';self.close();return
        for key,_ in self.selector.select(min(.05,max(0,self.deadline-(time.monotonic()-self.started)))):
            try:data=os.read(key.fileobj.fileno(),1024)
            except BlockingIOError:continue
            if not data:self.selector.unregister(key.fileobj);continue
            room=8192-self.total;self.buffers[key.data].extend(data[:room]);self.total+=min(room,len(data))
            if len(data)>room:self.state='output-limit';self.close();return
        if not self.selector.get_map() and self.process.poll() is not None:
            self.state='complete' if self.process.returncode==0 else 'child-failed'
            self.close()

    def await_ready(self):
        """Return only the first bounded JSON line; retain session for inspection."""
        while not self.closed:
            if b'\n' in self.buffers['stdout']:
                line=self.buffers['stdout'].split(b'\n',1)[0]
                if self.buffers['stderr']:self.state='warning';self.close();raise ValueError('unexpected stderr')
                try:
                    def unique(pairs):
                        value={}
                        for k,v in pairs:
                            if k in value:raise ValueError('duplicate')
                            value[k]=v
                        return value
                    value=json.loads(line,object_pairs_hook=unique)
                    if value.get('phase')!='ready':raise ValueError('not ready')
                except (ValueError,TypeError,AttributeError):
                    self.state='invalid-output';self.close();raise ValueError('invalid ready output')
                return value
            self.pump()
        raise ValueError('session ended before inspection readiness')

    def finish(self):
        while not self.closed:self.pump()
        return {'returncode':self.process.returncode,'stdout':bytes(self.buffers['stdout']),
                'stderr':bytes(self.buffers['stderr']),'status':self.state,'argv_sha256':self.argv_hash,
                'remote_cleanup_required':self.operation=='run-proposal-only',
                'remote_cleanup_executed':False}

    def close(self):
        if self.closed:return
        self.closed=True;self.selector.close()
        if self.process.poll() is None:
            try:os.killpg(self.process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        try:self.process.wait(timeout=2)
        finally:self.process.stdout.close();self.process.stderr.close()


def live_entry(*_,**__):
    raise PermissionError('live supervisor disabled pending final technical review')
