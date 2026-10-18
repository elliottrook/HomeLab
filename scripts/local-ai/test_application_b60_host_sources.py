import hashlib
import json
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from application_b60_host_sources import HostSourceError, read_attested_source


class HostSourceTests(unittest.TestCase):
    def envelope(self):
        payload = {"completed": True, "guest_ids": ["104", "110", "116"]}
        digest = hashlib.sha256((json.dumps(payload, sort_keys=True,
                                             separators=(",", ":")) + "\n").encode()).hexdigest()
        return {"schema": "aster-source-observation.v1", "source": "source:a",
                "cycle": "2026-10-18", "observed_epoch": 100,
                "payload": payload, "payload_sha256": digest}

    def read(self, path, expected_digest=None, now_epoch=110, mutate=None):
        value = self.envelope()
        if mutate:
            mutate(value)
        raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        path.write_bytes(raw)
        file_info = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=0,
                                    st_nlink=1, st_size=len(raw))
        parent_info = SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=0)
        lstats = iter((file_info, parent_info, file_info))
        with patch.object(Path, "lstat", side_effect=lambda: next(lstats)):
            return read_attested_source(path, expected_source="source:a",
                                        expected_cycle="2026-10-18",
                                        expected_digest=expected_digest or value["payload_sha256"],
                                        now_epoch=now_epoch)

    def test_accepts_pinned_root_owned_envelope(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.read(Path(temp) / "source.json")
        self.assertTrue(result.verified)
        self.assertEqual(result.source, "source:a")

    def test_rejects_digest_cycle_future_and_hardlink_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.json"
            with self.assertRaisesRegex(HostSourceError, "digest"):
                self.read(path, expected_digest="0" * 64)
            with self.assertRaisesRegex(HostSourceError, "shape"):
                self.read(path, mutate=lambda value: value.update(cycle="2026-10-17"))
            with self.assertRaisesRegex(HostSourceError, "shape"):
                self.read(path, mutate=lambda value: value.update(observed_epoch=111))
            value = self.envelope(); path.write_text(json.dumps(value))
            file_info = SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=0,
                                        st_nlink=2, st_size=100)
            parent_info = SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=0)
            lstats = iter((file_info, parent_info, file_info))
            with patch.object(Path, "lstat", side_effect=lambda: next(lstats)), \
                 self.assertRaisesRegex(HostSourceError, "custody"):
                read_attested_source(path, expected_source="source:a",
                                     expected_cycle="2026-10-18",
                                     expected_digest=self.envelope()["payload_sha256"],
                                     now_epoch=110)


if __name__ == "__main__":
    unittest.main()
