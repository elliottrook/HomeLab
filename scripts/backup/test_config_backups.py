import datetime,importlib.util,pathlib,sqlite3,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
backup=load('backup','scripts/backup/truenas-app-configs.py')
check=load('checker','scripts/check-configuration-backups.py')
class BackupTests(unittest.TestCase):
 def test_live_wal_and_payload_exclusion(self):
  with tempfile.TemporaryDirectory() as root:
   p=pathlib.Path(root);src=p/'source';src.mkdir();db=sqlite3.connect(src/'settings.db')
   try:
    db.execute('pragma journal_mode=wal');db.execute('create table value(n)');db.execute('insert into value values(42)');db.commit()
    for name in ['film.mkv','book.epub','recording.mp4','track.flac']:(src/name).write_bytes(b'excluded')
    (src/'cache').mkdir();(src/'cache'/'payload').write_bytes(b'excluded');(src/'settings.json').write_text('{}')
    copied=[];backup.copy_config(src,p/'out',copied)
    self.assertEqual({x.name for x in (p/'out').iterdir()},{'settings.db','settings.json'})
    with sqlite3.connect(p/'out'/'settings.db') as restored:self.assertEqual(restored.execute('select n from value').fetchone(),(42,))
    self.assertEqual(len(copied),1)
   finally:db.close()
 def test_monitor_rejects_stale_failed_incomplete_or_media(self):
  now=datetime.datetime.now(datetime.timezone.utc);s={'created_utc':now.isoformat(),'apps':17,'sqlite_verified':18,'size_matches':True,'media_included':False,'failure':False}
  self.assertTrue(check.assess(s,now)[0])
  for change in [{'created_utc':(now-datetime.timedelta(hours=31)).isoformat()},{'failure':True},{'size_matches':False},{'media_included':True},{'apps':16},{'sqlite_verified':17}]:self.assertFalse(check.assess(dict(s,**change),now)[0])
if __name__=='__main__':unittest.main()
