"""Source adapter must not certify a year from partial household/ARR data."""

import sqlite3
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from unittest import TestCase

from video_archiver.retention_years_live import LiveYearConfig, collect_movie_years


class Session:
    def __init__(self, visible):
        self.visible = visible

    def __call__(self, url, _headers):
        user = url.split('/Users/')[1].split('/')[0]
        query = parse_qs(urlparse(url).query)
        start = int(query['StartIndex'][0])
        items = self.visible[user]
        return 200, {'Items': [{'Id': value} for value in items[start:start + 500]],
                     'TotalRecordCount': len(items)}


class LiveYearTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.data = root / 'data'
        (self.data / 'movies').mkdir(parents=True)
        (self.data / 'archive-movies').mkdir(parents=True)
        (self.data / 'movies' / 'a.mkv').write_bytes(b'a')
        (self.data / 'archive-movies' / 'b.mkv').write_bytes(b'b')
        self.jf = root / 'jellyfin.db'
        self.rad = root / 'radarr.db'
        with sqlite3.connect(self.jf) as db:
            db.executescript('''
                CREATE TABLE Users(Id TEXT);
                CREATE TABLE BaseItemProviders(ItemId TEXT, ProviderId TEXT, ProviderValue TEXT);
                CREATE TABLE BaseItems(Id TEXT, Path TEXT, ProductionYear INTEGER, Type TEXT);
                INSERT INTO Users VALUES ('u1'),('u2');
                INSERT INTO BaseItemProviders VALUES ('a','Tmdb','1'),('b','Tmdb','2');
                INSERT INTO BaseItems VALUES
                  ('a','/media/movies/a.mkv',1939,'MediaBrowser.Controller.Entities.Movies.Movie'),
                  ('b','/media/archive-movies/b.mkv',1939,'MediaBrowser.Controller.Entities.Movies.Movie');
            ''')
        with sqlite3.connect(self.rad) as db:
            db.executescript('''
                CREATE TABLE Movies(Id INTEGER,MovieMetadataId INTEGER,Path TEXT,MovieFileId INTEGER);
                CREATE TABLE MovieMetadata(Id INTEGER,TmdbId INTEGER,Year INTEGER);
                CREATE TABLE MovieFiles(Id INTEGER,MovieId INTEGER,RelativePath TEXT);
                INSERT INTO MovieMetadata VALUES (1,1,1939),(2,2,1939);
                INSERT INTO Movies VALUES (1,1,'/media/movie/movies',10),
                                          (2,2,'/media/movie/archive-movies',20);
                INSERT INTO MovieFiles VALUES (10,1,'a.mkv'),(20,2,'b.mkv');
            ''')
        self.config = LiveYearConfig(self.rad, self.jf, self.data,
                                     'http://jellyfin.invalid', 'fixture-key', 2)

    def test_complete_exact_cross_library_year_is_certified(self):
        result = collect_movie_years(self.config, today=date(2026, 11, 6),
                                     fetch=Session({'u1': ['a', 'b'], 'u2': ['a', 'b']}))
        self.assertEqual(result.counts, {1939: 2})
        self.assertEqual(result.held, 0)

    def test_missing_household_visibility_cannot_count_second_movie(self):
        result = collect_movie_years(self.config, today=date(2026, 11, 6),
                                     fetch=Session({'u1': ['a', 'b'], 'u2': ['a']}))
        self.assertEqual(result.counts, {1939: 1})

    def test_arr_year_conflict_cannot_count_second_movie(self):
        with sqlite3.connect(self.rad) as db:
            db.execute('UPDATE MovieMetadata SET Year=1940 WHERE Id=2')
        result = collect_movie_years(self.config, today=date(2026, 11, 6),
                                     fetch=Session({'u1': ['a', 'b'], 'u2': ['a', 'b']}))
        self.assertEqual(result.counts, {1939: 1})

    def test_changed_household_roster_aborts_inventory(self):
        config = LiveYearConfig(self.rad, self.jf, self.data,
                                'http://jellyfin.invalid', 'fixture-key', 7)
        with self.assertRaisesRegex(RuntimeError, 'roster'):
            collect_movie_years(config, today=date(2026, 11, 6),
                                fetch=Session({'u1': ['a', 'b'], 'u2': ['a', 'b']}))

    def test_concurrent_jellyfin_change_aborts_year_inventory(self):
        session = Session({'u1': ['a', 'b'], 'u2': ['a', 'b']})
        changed = False
        def mutating_fetch(url, headers):
            nonlocal changed
            if not changed:
                changed = True
                with sqlite3.connect(self.jf) as db:
                    db.execute('UPDATE BaseItems SET ProductionYear=1940 WHERE Id=\'b\'')
            return session(url, headers)
        with self.assertRaisesRegex(RuntimeError, 'changed during movie-year inventory'):
            collect_movie_years(self.config, today=date(2026, 11, 6),
                                fetch=mutating_fetch)
