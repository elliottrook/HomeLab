from contextlib import contextmanager
import io
import json
import threading
from http.client import HTTPConnection
import unittest
from unittest.mock import patch,Mock
import camera_proxy as proxy
import camera_source as source

JPEG=b'\xff\xd8synthetic-frame\xff\xd9'

class ViewerTests(unittest.TestCase):
    def test_fetch_only_on_viewing_rate_limit_stop_and_expiry(self):
        clock=[100.];fetch=Mock(return_value=JPEG);viewer=proxy.Viewer(fetch,lambda:clock[0])
        self.assertFalse(viewer.status()['active']);fetch.assert_not_called()
        with self.assertRaises(ValueError):viewer.image()
        viewer.start();fetch.assert_not_called();self.assertEqual(viewer.image(),JPEG);self.assertEqual(viewer.image(),JPEG)
        self.assertEqual(fetch.call_count,1);clock[0]+=2;viewer.image();self.assertEqual(fetch.call_count,2)
        viewer.stop();self.assertEqual(viewer.frame,b'')
        viewer.start();viewer.image();clock[0]+=301;viewer.expire();self.assertEqual(viewer.frame,b'')
        with self.assertRaises(ValueError):viewer.image()

    def test_failure_closes_view_instead_of_presenting_cached_image(self):
        clock=[100.];fetch=Mock(side_effect=[JPEG,RuntimeError('private-error')]);viewer=proxy.Viewer(fetch,lambda:clock[0]);viewer.start();viewer.image();clock[0]+=2
        with self.assertRaisesRegex(ValueError,'unavailable'):viewer.image()
        self.assertFalse(viewer.status()['active']);self.assertEqual(viewer.frame,b'');self.assertEqual(viewer.status()['failures'],1)

    def test_http_does_not_allow_foreign_origin_host_or_camera_path(self):
        server=proxy.Server(('127.0.0.1',0),proxy.Handler);fetch=Mock(return_value=JPEG)
        server.viewer=proxy.Viewer(fetch);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def request(method,path,body=None,headers=None):
            connection=HTTPConnection('127.0.0.1',server.server_port,timeout=3)
            h={'Host':'127.0.0.1:15102'};h.update(headers or {})
            connection.request(method,path,body=body,headers=h);reply=connection.getresponse();raw=reply.read();status=reply.status;connection.close();return status,raw
        try:
            self.assertEqual(request('GET','/status')[0],200);fetch.assert_not_called()
            self.assertEqual(request('GET','/api/front_of_house/latest.jpg?frame=1')[0],503);fetch.assert_not_called()
            self.assertEqual(request('GET','/status',headers={'Host':'192.168.1.140:15102'})[0],403)
            self.assertEqual(request('POST','/view/start',b'{}',{'Content-Type':'application/json','Origin':'http://external'})[0],403)
            self.assertEqual(request('GET','/api/another_camera/latest.jpg')[0],404)
            self.assertEqual(request('GET','/api/front_of_house/latest.jpg?url=private')[0],404)
            self.assertEqual(request('POST','/view/start',b'{}',{'Content-Type':'application/json'})[0],200)
            self.assertEqual(request('GET','/api/front_of_house/latest.jpg?frame=1'),(200,JPEG))
            self.assertEqual(request('POST','/view/stop',b'{}',{'Content-Type':'application/json'})[0],200)
        finally:server.shutdown();server.server_close();thread.join(timeout=2)

class SourceTests(unittest.TestCase):
    def opener(self,fps=5.1,frame=JPEG):
        class Reply:
            def __init__(self,raw,kind):self.raw=raw;self.status=200;self.headers={'Content-Type':kind}
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,limit):return self.raw[:limit]
        opener=Mock();opener.open.side_effect=[Reply(json.dumps({'cameras':{'front_of_house':{'camera_fps':fps}}}).encode(),'application/json'),Reply(frame,'image/jpeg')]
        return opener
    def test_only_fixed_live_camera_is_read(self):
        opener=self.opener();self.assertEqual(source.read_camera(opener),JPEG)
        self.assertEqual([call.args[0] for call in opener.open.call_args_list],['http://127.0.0.1:5000/api/stats','http://127.0.0.1:5000/api/front_of_house/latest.jpg'])
    def test_stalled_camera_bad_jpeg_and_size_refused(self):
        for fps in (0,-1,True,float('nan'),999):
            with self.assertRaises(ValueError):source.read_camera(self.opener(fps))
        for frame in (b'not-jpeg',b'\xff\xd8'+b'x'*2097152+b'\xff\xd9'):
            with self.assertRaises(ValueError):source.read_camera(self.opener(frame=frame))
    def test_wrong_source_or_shell_command_has_no_http_effect(self):
        for address,command in (('192.168.1.157','aster-camera-front-v1'),('192.168.1.140','id')):
            with patch.dict('os.environ',dict(SSH_CONNECTION=address+' 1234 192.168.20.10 22',SSH_ORIGINAL_COMMAND=command),clear=True),patch('sys.argv',['frame.py']),patch.object(source,'read_camera') as read:
                self.assertEqual(source.main(),1);read.assert_not_called()

if __name__=='__main__':unittest.main()
