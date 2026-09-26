"""Authority/read tests use temporary records and stub one-shot; never network."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import s0_live_candidate as live
import s0_verified_read as reader


def record():
    return {'format':'s0-fixture-approval.v1','scope':copy.deepcopy(live.SCOPE),
            'provenance':copy.deepcopy(live.PROVENANCE),'reviewed_manifest_sha256':'a'*64,
            'release':{'technical_review':'passed','exclusive_operator_window':'confirmed','one_shot_execution':'released'}}


class VerifiedReadTests(unittest.TestCase):
    def test_regular_owner_bounded_and_no_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'file';p.write_bytes(b'hello')
            self.assertEqual(reader.read_owned_regular(p,5),b'hello')
            with self.assertRaises(ValueError):reader.read_owned_regular(p,4)
            with self.assertRaises(ValueError):reader.read_owned_regular(root,100)
            link=root/'link';link.symlink_to(p)
            with self.assertRaises(OSError):reader.read_owned_regular(link,10)
            directory=root/'linked-directory';directory.symlink_to(root,target_is_directory=True)
            with self.assertRaises(OSError):reader.read_owned_regular(directory/'file',10)
            with patch.object(reader.os,'geteuid',return_value=os.getuid()+1),self.assertRaises(ValueError):reader.read_owned_regular(p,10)
            p.chmod(0o666)
            with self.assertRaises(ValueError):reader.read_owned_regular(p,10)

    def test_hardlinks_and_fifo_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'file';p.write_bytes(b'x');os.link(p,root/'hardlink')
            with self.assertRaises(ValueError):reader.read_owned_regular(p,10)
            fifo=root/'fifo';os.mkfifo(fifo)
            with self.assertRaises(ValueError):reader.read_owned_regular(fifo,10)

    def test_same_descriptor_detects_during_read_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'file';p.write_bytes(b'old')
            read=os.read;changed=[False]
            def mutate(fd,size):
                result=read(fd,size)
                if not changed[0]:
                    changed[0]=True
                    with p.open('wb') as f:f.write(b'changed')
                return result
            with patch.object(reader.os,'read',side_effect=mutate),self.assertRaises(ValueError):reader.read_owned_regular(p,32)

    def test_open_descriptor_does_not_follow_swapped_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'file';p.write_bytes(b'old');replacement=root/'replacement';replacement.write_bytes(b'new')
            read=os.read;changed=[False]
            def swap(fd,size):
                if not changed[0]:changed[0]=True;os.replace(replacement,p)
                return read(fd,size)
            # The old inode loses its link: descriptor metadata detects replacement.
            with patch.object(reader.os,'read',side_effect=swap),self.assertRaises(ValueError):reader.read_owned_regular(p,32)


class AuthorityGateTests(unittest.TestCase):
    def test_released_record_calls_only_stub_prepared_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'approval.json';p.write_text(json.dumps(record()))
            with patch.object(live,'APPROVAL',p),patch.object(live,'verify_bundle',return_value={}) as verify,patch.object(live,'_prepared_one_shot',return_value={'status':'stub'}) as prepared,patch.object(live.sys,'argv',['launcher']):
                self.assertEqual(live.invoke_once(),{'status':'stub'})
                verify.assert_called_once_with('a'*64);prepared.assert_called_once_with('a'*64)

    def test_pending_scope_pin_and_extra_argument_rejected(self):
        for alteration in ('pending','scope','identity','pin','extra','duplicate'):
            with self.subTest(alteration=alteration),tempfile.TemporaryDirectory() as tmp:
                value=record()
                if alteration=='pending':value['release']['one_shot_execution']='pending'
                if alteration=='scope':value['scope']['accepted_corpus_evaluation']=True
                if alteration=='identity':value['provenance']['cryptographic_identity_proof']=True
                raw=json.dumps(value)
                if alteration=='duplicate':raw=raw[:-1]+',"format":"s0-fixture-approval.v1"}'
                p=Path(tmp).resolve()/'approval.json';p.write_text(raw)
                with patch.object(live,'APPROVAL',p),patch.object(live,'verify_bundle',side_effect=ValueError('wrong pin') if alteration=='pin' else None),patch.object(live,'_prepared_one_shot') as prepared,patch.object(live.sys,'argv',['launcher','--approve'] if alteration=='extra' else ['launcher']):
                    with self.assertRaises((ValueError,PermissionError)):live.invoke_once()
                    prepared.assert_not_called()

    def test_missing_record_denies_before_prepared(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(live,'APPROVAL',Path(tmp).resolve()/'absent'),patch.object(live,'_prepared_one_shot') as prepared,patch.object(live.sys,'argv',['launcher']):
            with self.assertRaises(FileNotFoundError):live.invoke_once()
            prepared.assert_not_called()

    def test_real_released_record_uses_mocked_prepared_path_only(self):
        value=json.loads(reader.read_owned_regular(live.APPROVAL,8192))
        self.assertEqual(value['reviewed_manifest_sha256'],hashlib.sha256(reader.read_owned_regular(live.MANIFEST,32768)).hexdigest())
        self.assertEqual(value['scope'],live.SCOPE)
        self.assertEqual(value['release'],{'technical_review':'passed','exclusive_operator_window':'confirmed','one_shot_execution':'released'})
        with patch.object(live,'_prepared_one_shot',return_value={'status':'mock-only'}) as prepared,patch.object(live.sys,'argv',['launcher']):
            self.assertEqual(live.invoke_once(),{'status':'mock-only'})
            prepared.assert_called_once_with(value['reviewed_manifest_sha256'])


if __name__=='__main__':unittest.main()
