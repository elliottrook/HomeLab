"""A season with an extra Jellyfin episode must stay held."""

import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase

from video_archiver.retention_seasons_live import collect_season_paths


class SeasonPathTests(TestCase):
    def test_duplicate_sonarr_path_holds_both_scopes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            folder = data / "archive-tv" / "Show"
            folder.mkdir(parents=True)
            (folder / "one.mkv").write_bytes(b"one")
            sonarr = root / "sonarr.db"
            jellyfin = root / "jellyfin.db"
            with sqlite3.connect(sonarr) as db:
                db.executescript("""
                    CREATE TABLE Series(Id INTEGER,Path TEXT);
                    CREATE TABLE Episodes(EpisodeFileId INTEGER,SeriesId INTEGER,SeasonNumber INTEGER);
                    CREATE TABLE EpisodeFiles(Id INTEGER,SeriesId INTEGER,SeasonNumber INTEGER,RelativePath TEXT);
                    INSERT INTO Series VALUES (1,'/media/tv/archive-tv/Show');
                    INSERT INTO Episodes VALUES (10,1,1),(20,1,2);
                    INSERT INTO EpisodeFiles VALUES (10,1,1,'one.mkv'),(20,1,2,'one.mkv');
                """)
            with sqlite3.connect(jellyfin) as db:
                db.executescript("""
                    CREATE TABLE BaseItems(Path TEXT,ParentIndexNumber INTEGER,Type TEXT);
                    INSERT INTO BaseItems VALUES
                      ('/media/archive-tv/Show/one.mkv',1,'MediaBrowser.Controller.Entities.TV.Episode');
                """)
            result = collect_season_paths(sonarr, jellyfin, data)
            self.assertEqual(result.exact_file_rows, 0)
            self.assertEqual(result.exact_season_scopes, 0)
            self.assertEqual(result.held_reasons, {"duplicate Sonarr file path": 2})

    def test_extra_jellyfin_episode_holds_its_season(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            series = data / "archive-tv" / "Show"
            series.mkdir(parents=True)
            (series / "one.mkv").write_bytes(b"one")
            (series / "two.mkv").write_bytes(b"two")
            sonarr = root / "sonarr.db"
            jellyfin = root / "jellyfin.db"
            with sqlite3.connect(sonarr) as db:
                db.executescript("""
                    CREATE TABLE Series(Id INTEGER,Path TEXT);
                    CREATE TABLE Episodes(EpisodeFileId INTEGER,SeriesId INTEGER,SeasonNumber INTEGER);
                    CREATE TABLE EpisodeFiles(Id INTEGER,SeriesId INTEGER,SeasonNumber INTEGER,RelativePath TEXT);
                    INSERT INTO Series VALUES (1,'/media/tv/archive-tv/Show');
                    INSERT INTO Episodes VALUES (10,1,1),(20,1,2);
                    INSERT INTO EpisodeFiles VALUES (10,1,1,'one.mkv'),(20,1,2,'two.mkv');
                """)
            with sqlite3.connect(jellyfin) as db:
                db.executescript("""
                    CREATE TABLE BaseItems(Path TEXT,ParentIndexNumber INTEGER,Type TEXT);
                    INSERT INTO BaseItems VALUES
                      ('/media/archive-tv/Show/one.mkv',1,'MediaBrowser.Controller.Entities.TV.Episode'),
                      ('/media/archive-tv/Show/two.mkv',2,'MediaBrowser.Controller.Entities.TV.Episode'),
                      ('/media/archive-tv/Show/extra.mkv',2,'MediaBrowser.Controller.Entities.TV.Episode');
                """)
            result = collect_season_paths(sonarr, jellyfin, data)
            self.assertEqual(result.sonarr_file_rows, 2)
            self.assertEqual(result.exact_file_rows, 2)
            self.assertEqual(result.season_scopes, 2)
            self.assertEqual(result.exact_season_scopes, 1)
            self.assertEqual(result.held_reasons, {"unowned Jellyfin episode in series root": 1})
