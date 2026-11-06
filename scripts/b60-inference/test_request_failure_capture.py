import json,tempfile,unittest
from pathlib import Path
from request_failure_capture import capture,MAXIMUM


def response(content='42',finish='stop',reasoning='private synthetic thought',**usage):
    return 200,json.dumps({'choices':[{'message':{'content':content,'reasoning_content':reasoning},'finish_reason':finish}], 'usage':usage}).encode()

class Tests(unittest.TestCase):
    def run_capture(self,results,clock=None):
        self.calls=[];values=iter(results);times=iter(clock or [0,1,2,3])
        def transport(payload,**bounds):
            self.calls.append((json.loads(payload),bounds));value=next(values)
            if isinstance(value,Exception):raise value
            return value
        return capture(transport,lambda:next(times))
    def test_second_length_retains_first_and_failure_metadata(self):
        packet=self.run_capture([response(),response('',finish='length',completion_tokens=1024,
            completion_tokens_details={'reasoning_tokens':1024})])
        self.assertEqual(packet['state'],'failed');self.assertEqual(packet['attempted_requests'],2)
        first,last=packet['records'];self.assertEqual(first['outcome'],'returned_unscored')
        self.assertEqual(last['outcome'],'token_limit');self.assertEqual(last['finish_reason'],'length')
        self.assertEqual(last['completion_tokens'],1024);self.assertEqual(last['reasoning_tokens'],1024)
        self.assertEqual(last['elapsed_ms'],1000);self.assertIsNone(last['answer_sha256'])
        self.assertNotIn('private synthetic thought',json.dumps(packet));self.assertNotIn('content',last)
    def test_timeout_retained_and_zero_retry(self):
        p=self.run_capture([TimeoutError('do not export this')])
        self.assertEqual(p['records'][0]['outcome'],'timeout');self.assertEqual(len(self.calls),1)
        self.assertEqual(p['attempted_requests'],1);self.assertEqual(p['planned_requests'],2)
        self.assertNotIn('do not export',json.dumps(p));self.assertEqual(p['retries'],0)
    def test_abnormal_token_numbers_are_unknown_without_losing_rows(self):
        p=self.run_capture([response(completion_tokens=2**100),response('',finish='length',
            completion_tokens_details={'reasoning_tokens':2**100})])
        self.assertEqual(len(p['records']),2)
        self.assertIsNone(p['records'][0]['completion_tokens'])
        self.assertIsNone(p['records'][1]['reasoning_tokens'])
    def test_http_malformed_oversized_and_invalid_type(self):
        for value,outcome in [((503,b'private server body'),'http_error'),((200,b'not json'),'malformed_response'),
                ((200,b'x'*(MAXIMUM+1)),'response_too_large'),((True,b'{}'),'invalid_http_status'),
                ((200,'private text'),'invalid_response_type')]:
            with self.subTest(outcome=outcome):
                p=self.run_capture([value]);self.assertEqual(p['records'][0]['outcome'],outcome)
                self.assertEqual(len(self.calls),1);self.assertNotIn('private',json.dumps(p))
    def test_transport_exception_text_never_exported(self):
        p=self.run_capture([OSError('Bearer forbidden-secret')])
        self.assertEqual(p['records'][0]['outcome'],'transport_error')
        self.assertNotIn('forbidden',json.dumps(p))
    def test_empty_final_and_unknown_finish_not_accepted(self):
        for value,code in [(response(''),'empty_final'),(response(finish='Bearer forbidden-secret'),'unsupported_finish')]:
            p=self.run_capture([value]);self.assertEqual(p['records'][0]['outcome'],code)
            self.assertNotIn('forbidden',json.dumps(p));self.assertFalse(p['model_qualified'])
    def test_late_valid_response_keeps_elapsed_but_fails(self):
        p=self.run_capture([response()],clock=[0,61]);r=p['records'][0]
        self.assertEqual(r['outcome'],'deadline_exceeded');self.assertEqual(r['elapsed_ms'],61000)
        self.assertIsNone(r['answer_sha256']);self.assertEqual(len(self.calls),1)
    def test_invalid_clock_before_and_after_attempt(self):
        p=self.run_capture([],clock=[float('nan')]);self.assertEqual(p['attempted_requests'],0)
        p=self.run_capture([response()],clock=[3,2]);self.assertEqual(p['attempted_requests'],1)
        self.assertEqual(p['records'][0]['outcome'],'invalid_clock');self.assertIsNone(p['records'][0]['answer_sha256'])
    def test_success_preserves_fixed_payload_and_does_not_claim_review(self):
        p=self.run_capture([response(completion_tokens=7),response('Ambiguous; inspect battery status.')])
        self.assertEqual(p['state'],'complete_unscored');self.assertTrue(p['records'][0]['arithmetic_exact'])
        self.assertFalse(p['semantic_review_performed']);self.assertFalse(p['ready_for_live_execution'])
        self.assertIsNone(p['records'][1]['completion_tokens'])
        for payload,bounds in self.calls:
            self.assertEqual(payload['max_tokens'],1024);self.assertFalse(payload['stream'])
            self.assertEqual(bounds,{'timeout_seconds':60,'maximum_bytes':MAXIMUM+1})
    def test_source_drift_rejected_before_interpretation_or_transport(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'source.py';marker=Path(d)/'marker'
            path.write_text('from pathlib import Path\nPath('+repr(str(marker))+').touch()')
            with self.assertRaises(ValueError):capture(lambda *a,**kw:self.fail('called'),lambda:0,source_path=path)
            self.assertFalse(marker.exists())
if __name__=='__main__':unittest.main()
