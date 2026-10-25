import copy,importlib.util,io,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from books_progress import Scope,Progress
from books_progress_reader import Account

source=Path(__file__).parent.parent/'plugin.audio.asterbooks/resources/lib/bridge.py'
spec=importlib.util.spec_from_file_location('resources.lib.bridge',source)
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
with patch.dict(sys.modules,{'resources.lib.bridge':base}):
    import books_sync_bridge

class SyncBridgeTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.bridge=books_sync_bridge.ProgressBridge('https://example.invalid','not-a-real-key-000000',Path(tmp.name)/'journal')
        self.bridge.http=SimpleNamespace(server_port=12345)
        self.account=Account('tv','user',False,tuple((k,False) for k in ('update','delete','upload')))
        self.bridge.writer.account=lambda:self.account
        self.reads=0;self.progress=None
        def read(*args):self.reads+=1;return self.progress
        self.bridge.reader.progress=read
        self.metadata={'id':'book','mediaType':'book','media':{'audioFiles':[{'ino':1,'duration':100,'metadata':{'filename':'book.m4b'}}],
            'chapters':[dict(title='One',start=0,end=50),dict(title='Two',start=50,end=100)]}}
        self.bridge.metadata=lambda _:self.metadata
    def test_book_resume_and_chapters_have_distinct_bound_capabilities(self):
        self.progress=Progress(Scope('tv','audiobook','book'),100,30,False,False,1)
        entries=self.bridge.describe('audiobook','book')
        self.assertEqual(len(entries),3);self.assertEqual(self.reads,1)
        self.assertEqual(entries[0]['number'],'R');self.assertEqual(entries[0]['start_offset'],30)
        self.assertEqual(len({e['url'] for e in entries}),3)
        self.assertTrue(self.bridge.registry.get(entries[0]['url']).resume)
        self.assertFalse(self.bridge.registry.get(entries[2]['url']).resume)
        self.assertEqual(self.bridge.registry.get(entries[2]['url']).offset,50)
    def test_missing_progress_never_does_one_read_per_chapter(self):
        entries=self.bridge.describe('audiobook','book');self.assertEqual(len(entries),2);self.assertEqual(self.reads,1)
    def test_podcast_episode_ids_not_guessed_from_row_or_title(self):
        self.metadata=dict(id='show',mediaType='podcast',media=dict(episodes=[
            dict(id='one',title='same',audioFile=dict(ino=2,duration=100)),
            dict(id='two',title='same',audioFile=dict(ino=3,duration=150))]))
        entries=self.bridge.describe('podcast','show')
        self.assertEqual([self.bridge.registry.get(e['url']).scope.episode for e in entries],['one','two'])
        self.assertEqual([e['episode_id'] for e in entries],['one','two'])
        self.assertTrue(all(self.bridge.registry.get(e['url']).resume for e in entries))
        self.assertEqual(self.reads,0)  # Fresh read occurs when a bound episode plays.
    def test_unverified_multi_file_stays_playable_without_bindings(self):
        self.metadata['media']['audioFiles'].append(dict(ino=4,duration=100,metadata=dict(filename='part2')))
        self.metadata['media']['chapters']=[]
        entries=self.bridge.describe('audiobook','book')
        self.assertEqual(len(entries),2)
        self.assertTrue(all(self.bridge.registry.get(e['url']) is None for e in entries))
        self.assertTrue(all('multi-file' in e['progress_sync'] for e in entries))
    def test_ambiguous_podcast_inode_never_bound(self):
        self.metadata=dict(id='show',mediaType='podcast',media=dict(episodes=[
            dict(id='one',title='same',audioFile=dict(ino=2,duration=100)),dict(id='two',title='same',audioFile=dict(ino=2,duration=100))]))
        entries=self.bridge.describe('podcast','show')
        self.assertTrue(all(self.bridge.registry.get(e['url']) is None for e in entries))
    def test_capability_pool_has_a_hard_bound_before_generation(self):
        self.bridge.capabilities={str(i):('book','1',self.bridge.clock()+100) for i in range(6501)}
        with patch.dict(sys.modules,{'resources.lib.bridge':base}),self.assertRaises(base.BridgeError):self.bridge.describe('audiobook','book')
        self.assertEqual(len(self.bridge.capabilities),6501)
    def multifile(self):
        self.metadata['media']=dict(audioFiles=[
            dict(ino=1,index=1,duration=100,metadata=dict(filename='z.mp3')),
            dict(ino=2,index=2,duration=150,metadata=dict(filename='a.mp3'))],
            tracks=[dict(ino=1,index=1,duration=100,startOffset=0),dict(ino=2,index=2,duration=150,startOffset=100)],
            chapters=[dict(title='A',start=0,end=100),dict(title='B',start=100,end=250)])
    def test_multifile_resume_uses_actual_second_file_not_first_entry(self):
        self.multifile();self.progress=Progress(Scope('tv','audiobook','book'),250,130,False,False,1)
        entries=self.bridge.describe('audiobook','book');resume=entries[0]
        binding=self.bridge.registry.get(resume['url'])
        self.assertEqual((binding.index,binding.offset),(1,30))
        self.assertEqual(resume['resume_position'],130)
        self.assertEqual(resume['title'],'Resume · 0:02:10')
        self.assertEqual(resume['duration'],120)  # Not the displayed resume time.
        self.assertEqual(self.bridge.lookup(__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(resume['url']).path)[1],'2')
        self.assertEqual(self.bridge.registry.get(entries[2]['url']).index,1)
        self.assertEqual(self.bridge.registry.get(entries[2]['url']).offset,0)
        self.assertFalse(self.bridge.registry.get(entries[2]['url']).resume)
    def test_multifile_file_rows_without_chapters_have_global_indices(self):
        self.multifile();self.metadata['media']['chapters']=[]
        entries=self.bridge.describe('audiobook','book')
        self.assertEqual([self.bridge.registry.get(e['url']).index for e in entries],[0,1])
    def test_ambiguous_track_maps_never_bind(self):
        self.multifile();original=copy.deepcopy(self.metadata)
        changes=[lambda m:m['tracks'].reverse(),lambda m:m['tracks'][1].update(ino=1),
            lambda m:m['tracks'][1].update(startOffset=90),lambda m:m['tracks'][1].update(duration=151),
            lambda m:m['audioFiles'][1].update(ino=1),lambda m:m['audioFiles'][1].update(index=1),
            lambda m:m['audioFiles'][1].update(exclude=True),lambda m:m['tracks'][1].update(error='bad'),
            lambda m:m['tracks'][1].update(index=True)]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                self.metadata=copy.deepcopy(original);change(self.metadata['media'])
                entries=self.bridge.describe('audiobook','book')
                self.assertTrue(entries);self.assertTrue(all(self.bridge.registry.get(e['url']) is None for e in entries))
