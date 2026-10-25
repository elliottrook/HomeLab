"""Passing reproductions of an unsafe ABS upsert race, NOT enablement gates.

No network or real data. Keep this counterexample: client preflight/read-back
cannot certify strict create-only behavior against an upserting server.
"""
import tempfile,unittest
from pathlib import Path
from books_bookmark_trial import Bookmark,State,BookmarkTrial

class UpsertHazardTests(unittest.TestCase):
    def test_server_upsert_can_rename_an_existing_timestamp(self):
        old=Bookmark('book',42,'Family note',1000)
        # Semantic model of the deployed POST contract, not a proposed writer.
        def server_post(existing,title):
            return Bookmark(existing.item,existing.time,title,existing.created)
        after=server_post(old,'Another client note')
        self.assertEqual(after.created,old.created)
        self.assertNotEqual(after.title,old.title)

    def test_preflight_then_post_race_can_falsely_certify_disposable_ownership(self):
        with tempfile.TemporaryDirectory() as folder:
            rows=[];calls=[];account='a'*64;progress='b'*64
            foreign=Bookmark('book',42,'Other client wins the gap',1000)
            def read():return State(account,tuple(sorted(rows)),progress)
            def create(item,payload):
                # A concurrent client arrives AFTER the last preflight GET.
                rows.append(foreign)
                renamed=Bookmark(item,payload['time'],payload['title'],foreign.created)
                rows[-1]=renamed;calls.append('upsert-renamed-foreign')
                return renamed.row()
            def remove(record):rows.remove(record);calls.append('deleted-foreign-identity');return True
            trial=BookmarkTrial(read,create,remove,Path(folder)/'trial',account,'book',42,'Aster lab bookmark race-reproduction')
            result=trial.run()
            self.assertTrue(result['passed'])  # Demonstrates why this is insufficient.
            self.assertEqual(calls,['upsert-renamed-foreign','deleted-foreign-identity'])
            self.assertFalse(rows)
