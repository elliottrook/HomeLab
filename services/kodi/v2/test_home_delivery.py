from copy import deepcopy
from datetime import timedelta
import importlib.util
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

from home_delivery import prepare, decode_guest_reply, MAX_CAPTURE_BYTES
from test_home_preview import fixture
from test_home_freshness import NOW

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('check_home_delivery', HERE/'tools/check_home_delivery.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def capture(snapshot=None, age=0):
    stamp = int((NOW - timedelta(seconds=age)).timestamp())
    metadata = '1|234|350|' + str(stamp) + '|' + str(stamp) + '|600|1|mtime-ns|ctime-ns'
    return dict(capture_version=1, before=metadata, after=metadata,
                snapshot=fixture()['snapshot'] if snapshot is None else snapshot)


def raw(value):
    return json.dumps(value, ensure_ascii=True).encode('ascii')


class CaptureTests(unittest.TestCase):
    def test_valid_candidate_keeps_source_time_and_is_not_in_repr(self):
        value = capture(age=45); before = deepcopy(value)
        result = prepare(raw(value), NOW)
        payload = json.loads(result.encoded)
        self.assertEqual(payload['source_updated_at'], (NOW-timedelta(seconds=45)).isoformat())
        self.assertEqual(payload['generated_at'], NOW.isoformat())
        self.assertEqual(payload['snapshot'], value['snapshot'])
        self.assertEqual(result.counts, (1, 1, 1))
        self.assertNotIn('laundry', repr(result))
        self.assertNotIn('20.5', repr(result))
        self.assertEqual(value, before)

    def test_old_source_cannot_be_revived_by_new_publication(self):
        for age in (601, 3600, -301):
            with self.assertRaisesRegex(ValueError, r'^home-capture-(stale|future)$'):
                prepare(raw(capture(age=age)), NOW)
        self.assertEqual(prepare(raw(capture(age=600)), NOW).counts, (1, 1, 1))

    def test_capture_changed_inode_or_metadata_is_refused(self):
        for after in ('2|different', None, 'a'*401):
            value = capture(); value['after'] = after
            with self.assertRaisesRegex(ValueError, '^home-capture-source-changed$'):
                prepare(raw(value), NOW)

    def test_bad_metadata_permissions_links_sizes_and_times_are_refused(self):
        for index, bad in ((2,'0'),(2,'262145'),(2,'true'),(3,'-1'),(3,'9'*20),
                           (5,'644'),(6,'2'),(7,''),(8,'x'*81)):
            value=capture(); parts=value['before'].split('|'); parts[index]=bad
            value['before']=value['after']='|'.join(parts)
            with self.assertRaisesRegex(ValueError, '^home-capture-[a-z-]+$'):
                prepare(raw(value), NOW)

    def test_strict_capture_schema_unknown_fields_and_cameras_are_refused(self):
        variants = []
        for key, bad in (('capture_version',True),('capture_version',1.0),
                         ('capture_version',2),('extra','private')):
            value=capture();value[key]=bad;variants.append(value)
        for key,bad in (('cameras',[]),('secret','never-transport-this')):
            value=capture();value['snapshot'][key]=bad;variants.append(value)
        value=capture();del value['snapshot']['lights'];variants.append(value)
        value=capture();value['snapshot']['schema_version']=True;variants.append(value)
        for value in variants:
            with self.assertRaisesRegex(ValueError, '^home-capture-[a-z-]+$'):
                prepare(raw(value),NOW)

    def test_nested_fields_aliases_and_values_are_revalidated_locally(self):
        for field,bad in (('alias','secret-location'),('value',True),('value',999),
                          ('url','https://private.example'),('unit','K')):
            value=capture();value['snapshot']['temperatures'][0][field]=bad
            with self.assertRaisesRegex(ValueError,'^home-capture-invalid$'):
                prepare(raw(value),NOW)

    def test_json_duplicate_oversize_invalid_and_error_privacy(self):
        for value in (b'', b'x'*(MAX_CAPTURE_BYTES+1), b'\xff', b'null', b'[]',
                      b'{"private-leak":', b'['*2000, b'{"before":1,"before":2}',
                      b'{"snapshot":{"a":1,"a":2}}', b'{"x":NaN}'):
            with self.assertRaisesRegex(ValueError,'^home-capture-[a-z-]+$') as raised:
                prepare(value,NOW)
            self.assertNotIn('private-leak',str(raised.exception))
        with self.assertRaisesRegex(ValueError,'^home-capture-aware-clock$'):
            prepare(raw(capture()),NOW.replace(tzinfo=None))

    def test_guest_exit_truncation_shape_and_errors_fail_without_payload_leaks(self):
        good=dict(exitcode=0,exited=1,**{'out-data':raw(capture()).decode(),'out-truncated':0})
        self.assertEqual(decode_guest_reply(raw(good)),raw(capture()))
        for key,bad in (('exitcode',1),('exitcode',False),('exited',0),('exited',True),
                         ('out-truncated',1),('out-truncated',False),('err-truncated',True),
                         ('err-data','PRIVATE-MESSAGE'),('out-data',None),('extra','PRIVATE-MESSAGE')):
            value=deepcopy(good);value[key]=bad
            with self.assertRaisesRegex(ValueError,'^home-capture-[a-z-]+$') as raised:
                decode_guest_reply(raw(value))
            self.assertNotIn('PRIVATE',str(raised.exception))
        for value in (b'not-json', b'x'*1048577, b'{"exited":1,"exited":1}'):
            with self.assertRaisesRegex(ValueError,'^home-capture-[a-z-]+$'):
                decode_guest_reply(value)


class SourceCheckTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('jq'), 'jq needed for source-local boundary evaluation')
    def test_actual_source_jq_filter_preserves_only_reviewed_valid_snapshot(self):
        value=fixture()['snapshot']
        reply=subprocess.run(['jq','-ace',checker.source_filter()],input=raw(value),capture_output=True)
        self.assertEqual(reply.returncode,0,reply.stderr)
        self.assertEqual(json.loads(reply.stdout),value)
        for mutation in ('token','camera','alias','temperature','humidity','condition','light','array'):
            candidate=deepcopy(value)
            if mutation=='token':candidate['token']='PRIVATE'
            elif mutation=='camera':candidate['cameras']=[]
            elif mutation=='alias':candidate['temperatures'][0]['alias']='PRIVATE'
            elif mutation=='temperature':candidate['temperatures'][0]['value']=999
            elif mutation=='humidity':candidate['weather'][0]['humidity']=True
            elif mutation=='condition':candidate['weather'][0]['condition']='PRIVATE'
            elif mutation=='light':candidate['lights'][0]['url']='PRIVATE'
            elif mutation=='array':candidate['lights']=[candidate['lights'][0]]*2
            reply=subprocess.run(['jq','-ace',checker.source_filter()],input=raw(candidate),capture_output=True)
            self.assertNotEqual(reply.returncode,0,mutation)
            self.assertEqual(reply.stdout,b'',mutation)

    def test_fixed_source_ssh_and_no_file_publication_or_camera_request(self):
        command=shlex.split(checker.source_command())
        self.assertEqual(command[:7],['qm','guest','exec','103','--','sh','-c'])
        self.assertIn(checker.SOURCE,command[7])
        self.assertEqual(command[7].count('stat -c'),3)
        self.assertIn('head -c 262145',command[7])
        for banned in ('curl','frigate','scp','rsync','mktemp','chmod','mv ', 'sleep', 'tee ', '>>'):
            self.assertNotIn(banned,command[7])
        guest=dict(exitcode=0,exited=1,**{'out-truncated':0,'out-data':raw(capture()).decode()})
        with patch.object(checker.subprocess,'run',return_value=type('Reply',(),dict(stdout=raw(guest)))()) as run:
            with patch.object(checker,'datetime') as clock:
                clock.now.return_value=NOW
                result=checker.check_source()
        self.assertFalse(result['published']);self.assertFalse(result['hp_changed'])
        self.assertNotIn('laundry',repr(result))
        self.assertEqual(run.call_args.args[0][:6],['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','proxmox'])
        self.assertTrue(run.call_args.kwargs['check'])
        self.assertLessEqual(run.call_args.kwargs['timeout'],25)

    def test_checker_failure_does_not_print_ssh_stderr_or_raw_payload(self):
        from contextlib import redirect_stdout
        import io
        output=io.StringIO()
        with patch.object(checker.sys,'argv',['check_home_delivery.py']), \
             patch.object(checker,'check_source',side_effect=subprocess.CalledProcessError(1,'PRIVATE',stderr=b'PRIVATE')), \
             redirect_stdout(output):
            self.assertEqual(checker.main(),1)
        self.assertNotIn('PRIVATE',output.getvalue())
        self.assertEqual(json.loads(output.getvalue())['code'],'home-check-transport-failed')
