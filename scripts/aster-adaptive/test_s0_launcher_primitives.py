"""Harmless disposable launcher primitive probes; not a corpus launcher.

Only constant invented children execute. No sockets, user configuration, accepted
corpus, model, engine source, deployment or dependency installation is accessed.
"""
import json
import os
import resource
import selectors
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


class LauncherPrimitives(unittest.TestCase):
    def child(self, source, cwd, stdout=subprocess.PIPE):
        return subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c', source],
                                cwd=cwd, env={'LANG': 'C', 'LC_ALL': 'C'},
                                stdin=subprocess.DEVNULL, stdout=stdout,
                                stderr=subprocess.PIPE, start_new_session=True,
                                close_fds=True)

    def test_parent_deadline_kills_owned_process_group(self):
        with tempfile.TemporaryDirectory(prefix='s0-primitive-') as temp:
            child=self.child('import time; time.sleep(30)',temp)
            try:
                with self.assertRaises(subprocess.TimeoutExpired):child.communicate(timeout=.2)
                os.killpg(child.pid,signal.SIGKILL)
                child.communicate(timeout=3)
                self.assertEqual(child.returncode,-signal.SIGKILL)
            finally:
                if child.poll() is None:
                    os.killpg(child.pid,signal.SIGKILL);child.communicate(timeout=3)

    def test_environment_allowlist_and_isolated_python(self):
        source='import os,sys,json; initial=sorted(os.environ); os.environ.pop("__CF_USER_TEXT_ENCODING",None); print(json.dumps({"initial_keys":initial,"keys":sorted(os.environ),"isolated":sys.flags.isolated,"site":sys.flags.no_site,"bytecode":sys.dont_write_bytecode}))'
        with tempfile.TemporaryDirectory(prefix='s0-primitive-') as temp:
            child=self.child(source,temp);out,err=child.communicate(timeout=3)
            self.assertEqual(child.returncode,0);self.assertEqual(err,b'')
            data=json.loads(out)
            self.assertTrue(set(data['initial_keys']) <= {'LANG','LC_ALL','__CF_USER_TEXT_ENCODING'})
            self.assertEqual(data['keys'],['LANG','LC_ALL'])
            self.assertEqual((data['isolated'],data['site'],data['bytecode']),(1,1,True))

    def test_file_size_limit_in_disposable_child(self):
        # Child hard limit only; never alter the host user's or parent's limits.
        source='import os,resource; resource.setrlimit(resource.RLIMIT_FSIZE,(1024,1024)); f=os.open("fixture",os.O_CREAT|os.O_WRONLY,0o600); os.write(f,b"x"*4096); os.close(f)'
        with tempfile.TemporaryDirectory(prefix='s0-primitive-') as temp:
            child=self.child(source,temp);child.communicate(timeout=3)
            self.assertLessEqual((Path(temp)/'fixture').stat().st_size,1024)

    def test_parent_bounds_output_and_reaps_child(self):
        source='import os,time; os.write(1,b"x"*8192); time.sleep(30)'
        with tempfile.TemporaryDirectory(prefix='s0-primitive-') as temp:
            child=self.child(source,temp);selector=selectors.DefaultSelector();selector.register(child.stdout,selectors.EVENT_READ)
            retained=bytearray(); exceeded=False;deadline=time.monotonic()+3
            try:
                while time.monotonic()<deadline and not exceeded:
                    for key,_ in selector.select(.1):
                        chunk=os.read(key.fileobj.fileno(),1024)
                        if not chunk:break
                        remaining=1024-len(retained)
                        retained.extend(chunk[:remaining])
                        exceeded=len(chunk)>remaining
                        if exceeded:break
                self.assertTrue(exceeded);self.assertEqual(len(retained),1024)
            finally:
                selector.close()
                if child.poll() is None:os.killpg(child.pid,signal.SIGKILL)
                child.communicate(timeout=3)

    def test_exclusive_claim_and_atomic_same_directory_result(self):
        with tempfile.TemporaryDirectory(prefix='s0-primitive-') as temp:
            root=Path(temp);claim=root/'fixture-run'
            claim.mkdir(mode=0o700)
            with self.assertRaises(FileExistsError):claim.mkdir(mode=0o700)
            flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW
            fd=os.open(claim/'partial',flags,0o600)
            with os.fdopen(fd,'wb') as stream:
                stream.write(b'{"scope":"invented-fixture"}\n');stream.flush();os.fsync(stream.fileno())
            os.replace(claim/'partial',claim/'result.json')
            self.assertEqual(json.loads((claim/'result.json').read_text()),{'scope':'invented-fixture'})
            # Power-loss durability/dir-fsync is not claimed by rename alone.

    def test_interruption_marker_is_not_a_success_receipt(self):
        with tempfile.TemporaryDirectory(prefix='s0-primitive-') as temp:
            root=Path(temp);(root/'state.json').write_text('{"state":"running","scope":"invented-fixture"}')
            state=json.loads((root/'state.json').read_text())
            self.assertEqual(state['state'],'running');self.assertFalse((root/'result.json').exists())
            # Merely demonstrating conservative recovery interpretation; no real crash claimed.
            recovered={'state':'interrupted-unverified','previous':state['state']}
            self.assertNotEqual(recovered['state'],'complete')


if __name__=='__main__':unittest.main()
