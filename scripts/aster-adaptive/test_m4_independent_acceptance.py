import json
from pathlib import Path
import tempfile
import unittest

import m4_independent_acceptance as acceptance


def record():
    return {"schema":acceptance.SCHEMA,"reviewer":"independent-owner",
        "decision":"retain","accepted_commit":"a"*40,
        "artifact_sha256":acceptance.ARTIFACT_SHA256,
        "ledger_head":acceptance.LEDGER_HEAD,
        "custody_method":"human-controlled-offline-record",
        "custody_reference_sha256":"b"*64,"reviewed_at":"2026-10-27T03:00:00Z",
        "data_scope":"synthetic-only","private_collection_authorized":False,
        "authority":"not-granted","limits":["synthetic provenance only"]}


class AcceptanceTests(unittest.TestCase):
    def write(self,value):
        root=tempfile.TemporaryDirectory();self.addCleanup(root.cleanup)
        path=Path(root.name)/"record.json";path.write_text(json.dumps(value))
        return path

    def test_accepts_exact_human_record_without_granting_authority(self):
        value=acceptance.validate(self.write(record()))
        self.assertEqual(value["status"],"valid")
        self.assertEqual(value["authority"],"not-granted")

    def test_rejects_self_grant_wrong_artifact_and_missing_custody(self):
        changes=({"authority":"granted"},{"artifact_sha256":"c"*64},
                 {"custody_method":"repository"},{"private_collection_authorized":True})
        for change in changes:
            value=record();value.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):
                acceptance.validate(self.write(value))

    def test_rejects_duplicate_keys_and_non_utc_time(self):
        path=self.write(record());raw=path.read_text()
        path.write_text(raw[:-1]+',"authority":"not-granted"}')
        with self.assertRaisesRegex(ValueError,"duplicate"):
            acceptance.validate(path)
        value=record();value["reviewed_at"]="2026-10-26T20:00:00-07:00"
        with self.assertRaisesRegex(ValueError,"UTC"):
            acceptance.validate(self.write(value))


if __name__=="__main__":unittest.main()
