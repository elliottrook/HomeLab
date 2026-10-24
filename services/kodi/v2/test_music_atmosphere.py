from pathlib import Path
import sqlite3,tempfile,time,unittest
from types import SimpleNamespace
from unittest.mock import Mock,MagicMock,patch
from music_atmosphere import Atmosphere,BASE,DEFAULT,cached_path,wash,sample


class AtmosphereTests(unittest.TestCase):
    def test_colour_is_a_small_wash_not_a_second_art_image(self):
        for rgb in ((0,0,0),(255,255,255),(255,0,0),(0,255,0),(0,0,255)):
            colour=wash([rgb]);self.assertEqual(len(colour),8)
            self.assertTrue(all(abs(int(colour[2+i*2:4+i*2],16)-BASE[i])<=19 for i in range(3)))
        self.assertEqual(wash([(255,0,0,0)]),DEFAULT)
        self.assertEqual(wash([]),DEFAULT)

    def test_only_exact_cached_local_art_is_read_and_database_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);thumbs=root/'thumbs';(thumbs/'a').mkdir(parents=True)
            image=thumbs/'a'/'abcdef12.jpg';image.write_bytes(b'cached-art')
            database=root/'textures.db';connection=sqlite3.connect(database)
            connection.execute('CREATE TABLE texture(url TEXT,cachedurl TEXT)')
            connection.execute('INSERT INTO texture VALUES(?,?)',('https://private.invalid/art','a/abcdef12.jpg'))
            connection.commit();connection.close();before=database.read_bytes()
            self.assertEqual(cached_path('image://https%3A%2F%2Fprivate.invalid%2Fart/',database,thumbs),image.resolve())
            self.assertIsNone(cached_path('https://other.invalid/art',database,thumbs))
            self.assertEqual(database.read_bytes(),before)
            connection=sqlite3.connect(database)
            connection.execute('UPDATE texture SET cachedurl=?',('../outside.jpg',));connection.commit();connection.close()
            self.assertIsNone(cached_path('https://private.invalid/art',database,thumbs))

    def test_optional_worker_is_bounded_and_stale_colour_is_not_applied(self):
        now=[0];calls=[]
        def sampler(art,*args):calls.append(art);return 'ffe0d9c9'
        sampler_state=Atmosphere('db','thumbs',sampler=sampler,clock=lambda:now[0])
        self.assertEqual(sampler_state.poll('one'),DEFAULT)
        now[0]=2;sampler_state.poll('one');sampler_state.close()
        self.assertEqual(sampler_state.poll('two'),DEFAULT)
        now[0]=4;sampler_state.poll('two');sampler_state.close()
        self.assertEqual(sampler_state.poll('two'),'ffe0d9c9')
        self.assertEqual(calls,['one','two'])

    def test_missing_cache_has_only_three_attempts(self):
        now=[0];calls=[]
        state=Atmosphere('db','thumbs',sampler=lambda *args:calls.append(1),clock=lambda:now[0])
        for tick in range(12):
            now[0]=tick;state.poll('missing');state.close()
        self.assertEqual(len(calls),3);self.assertEqual(state.colour,DEFAULT)

    def test_oversized_image_is_rejected_before_decode(self):
        image=Mock(width=10000,height=10000);opened=MagicMock()
        opened.__enter__.return_value=image
        decoder=SimpleNamespace(open=Mock(return_value=opened))
        with (patch('music_atmosphere.cached_path',return_value=Path('synthetic')),
              patch.dict('sys.modules',{'PIL':SimpleNamespace(Image=decoder)})):
            self.assertIsNone(sample('art','db','thumbnails'))
        image.draft.assert_not_called();image.thumbnail.assert_not_called()
