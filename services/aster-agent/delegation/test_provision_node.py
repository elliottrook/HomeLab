"""Private protocol failure tests; all values are fictional, no network or vault."""
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import provision_node as node
import vault_provision


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        node._buffer=b''
        read,write=os.pipe()
        self.reader=os.fdopen(read,'rb',buffering=0)
        self.writer=os.fdopen(write,'wb',buffering=0)

    def tearDown(self):
        self.reader.close();self.writer.close();node._buffer=b''

    def test_partial_frame_times_out_without_waiting_for_newline(self):
        self.writer.write(b'{"unfinished":')
        started=time.monotonic()
        with patch.object(node.sys,'stdin',self.reader), patch.object(node,'FRAME_TIMEOUT',0.05):
            with self.assertRaisesRegex(ValueError,'unavailable'): node.receive()
        self.assertLess(time.monotonic()-started,1)

    def test_coalesced_frames_are_preserved(self):
        self.writer.write(b'{"one":1}\n{"two":2}\n')
        with patch.object(node.sys,'stdin',self.reader):
            self.assertEqual(node.receive(),{'one':1})
            self.assertEqual(node.receive(),{'two':2})

    def test_disconnected_partial_frame_fails(self):
        self.writer.write(b'{');self.writer.close()
        with patch.object(node.sys,'stdin',self.reader):
            with self.assertRaisesRegex(ValueError,'disconnected'): node.receive()

    def test_blocked_output_times_out_and_restores_descriptor(self):
        fd=self.writer.fileno();os.set_blocking(fd,False)
        try:
            while True: os.write(fd,b'x'*4096)
        except BlockingIOError: pass
        os.set_blocking(fd,True)
        with patch.object(node.sys,'stdout',self.writer), patch.object(node,'WRITE_TIMEOUT',0.05):
            with self.assertRaisesRegex(ValueError,'unavailable'): node.send('fixture',{})
        self.assertTrue(os.get_blocking(fd))


class Response(io.BytesIO):
    def __init__(self,value,status=200):
        super().__init__(json.dumps(value).encode());self.status=status


class VaultNodeTests(unittest.TestCase):
    def exercise(self,*,provision_failure=False,revoke_failure=False,version='2.6.4'):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'admin.token';path.write_text('fictional-admin');path.chmod(0o600)
            frames=[];calls=[];original=os.fstat
            def root_stat(fd):
                info=original(fd)
                values=list(info);values[4]=0
                return os.stat_result(values)
            class Opener:
                def open(self,request,timeout):
                    if isinstance(request,str): return Response({'version':version})
                    calls.append(request.full_url)
                    return Response({},500 if revoke_failure else 204)
            def provision(*args,**kwargs):
                if provision_failure: raise RuntimeError('fictional private detail')
                return {'complete':True}
            with patch.object(node,'ADMIN',path), patch.object(node,'receive',return_value={
                    'approved_sha256':vault_provision.fingerprint(),'credentials':{}}), \
                 patch.object(node,'send',side_effect=lambda kind,value:frames.append((kind,value))), \
                 patch.object(node,'acknowledged',side_effect=lambda kind,value:frames.append((kind,value)) or True), \
                 patch.object(node.ssl,'create_default_context'), \
                 patch.object(node.urllib.request,'build_opener',return_value=Opener()), \
                 patch.object(node.os,'fstat',side_effect=root_stat), \
                 patch.object(vault_provision,'provision',side_effect=provision):
                node.vault()
            return frames,calls,path.exists()

    def test_success_revokes_admin_and_removes_handoff(self):
        frames,calls,exists=self.exercise()
        self.assertFalse(exists)
        self.assertEqual(len(calls),1)
        self.assertTrue(calls[0].endswith('/auth/token/revoke-self'))
        self.assertEqual([kind for kind,_ in frames],['admin_revoked','vault_done'])

    def test_provision_failure_still_revokes_and_sanitizes(self):
        frames,calls,exists=self.exercise(provision_failure=True)
        self.assertFalse(exists);self.assertEqual(len(calls),1)
        self.assertEqual(frames[-1],('error',{'code':'vault_incomplete'}))
        self.assertNotIn('private detail',str(frames))

    def test_unconfirmed_revocation_retains_handoff_without_success(self):
        frames,_,exists=self.exercise(revoke_failure=True)
        self.assertTrue(exists)
        self.assertEqual(frames,[('error',{'code':'vault_incomplete'})])

    def test_wrong_version_never_enters_provisioning_or_revokes(self):
        frames,calls,exists=self.exercise(version='2.6.3')
        self.assertTrue(exists);self.assertEqual(calls,[])
        self.assertEqual(frames,[('error',{'code':'vault_incomplete'})])
