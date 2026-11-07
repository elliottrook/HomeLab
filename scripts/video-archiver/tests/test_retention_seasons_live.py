"""A season with an extra Jellyfin episode must stay held."""

import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from video_archiver import retention_seasons_live
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
                    CREATE TABLE Series(Id INTEGER,Path TEXT,TvdbId INTEGER);
                    CREATE TABLE Episodes(EpisodeFileId INTEGER,SeriesId INTEGER,SeasonNumber INTEGER);
                    CREATE TABLE EpisodeFiles(Id INTEGER,SeriesId INTEGER,SeasonNumber INTEGER,RelativePath TEXT);
                    INSERT INTO Series VALUES (1,'/media/tv/archive-tv/Show',101);
                    INSERT INTO Episodes VALUES (10,1,1),(20,1,2);
                    INSERT INTO EpisodeFiles VALUES (10,1,1,'one.mkv'),(20,1,2,'one.mkv');
                """)
            with sqlite3.connect(jellyfin) as db:
                db.executescript("""
                    CREATE TABLE BaseItems(Id TEXT,Path TEXT,ParentIndexNumber INTEGER,Type TEXT,SeriesId TEXT,SeasonId TEXT,IndexNumber INTEGER);
                    CREATE TABLE BaseItemProviders(ItemId TEXT,ProviderId TEXT,ProviderValue TEXT);
                    INSERT INTO BaseItems VALUES ('series','/media/archive-tv/Show',NULL,'MediaBrowser.Controller.Entities.TV.Series',NULL,NULL,NULL);
                    INSERT INTO BaseItems VALUES ('season1',NULL,NULL,'MediaBrowser.Controller.Entities.TV.Season','series',NULL,1);
                    INSERT INTO BaseItemProviders VALUES ('series','Tvdb','101');
                    INSERT INTO BaseItems VALUES
                      ('ep1','/media/archive-tv/Show/one.mkv',1,'MediaBrowser.Controller.Entities.TV.Episode','series','season1',NULL);
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
                    CREATE TABLE Series(Id INTEGER,Path TEXT,TvdbId INTEGER);
                    CREATE TABLE Episodes(EpisodeFileId INTEGER,SeriesId INTEGER,SeasonNumber INTEGER);
                    CREATE TABLE EpisodeFiles(Id INTEGER,SeriesId INTEGER,SeasonNumber INTEGER,RelativePath TEXT);
                    INSERT INTO Series VALUES (1,'/media/tv/archive-tv/Show',101);
                    INSERT INTO Episodes VALUES (10,1,1),(20,1,2);
                    INSERT INTO EpisodeFiles VALUES (10,1,1,'one.mkv'),(20,1,2,'two.mkv');
                """)
            with sqlite3.connect(jellyfin) as db:
                db.executescript("""
                    CREATE TABLE BaseItems(Id TEXT,Path TEXT,ParentIndexNumber INTEGER,Type TEXT,SeriesId TEXT,SeasonId TEXT,IndexNumber INTEGER);
                    CREATE TABLE BaseItemProviders(ItemId TEXT,ProviderId TEXT,ProviderValue TEXT);
                    INSERT INTO BaseItems VALUES ('series','/media/archive-tv/Show',NULL,'MediaBrowser.Controller.Entities.TV.Series',NULL,NULL,NULL);
                    INSERT INTO BaseItems VALUES ('season1',NULL,NULL,'MediaBrowser.Controller.Entities.TV.Season','series',NULL,1);
                    INSERT INTO BaseItems VALUES ('season2',NULL,NULL,'MediaBrowser.Controller.Entities.TV.Season','series',NULL,2);
                    INSERT INTO BaseItemProviders VALUES ('series','Tvdb','101');
                    INSERT INTO BaseItems VALUES
                      ('ep1','/media/archive-tv/Show/one.mkv',1,'MediaBrowser.Controller.Entities.TV.Episode','series','season1',NULL),
                      ('ep2','/media/archive-tv/Show/two.mkv',2,'MediaBrowser.Controller.Entities.TV.Episode','series','season2',NULL),
                      ('ep3','/media/archive-tv/Show/extra.mkv',2,'MediaBrowser.Controller.Entities.TV.Episode','series','season2',NULL);
                """)
            result = collect_season_paths(sonarr, jellyfin, data)
            self.assertEqual(result.sonarr_file_rows, 2)
            self.assertEqual(result.exact_file_rows, 2)
            self.assertEqual(result.season_scopes, 2)
            self.assertEqual(result.exact_season_scopes, 1)
            self.assertEqual(result.provider_certified_season_scopes, 1)
            self.assertEqual(result.certified_scope_item_ids[(1, 1)],
                             ('ep1', 'season1', 'series'))
            self.assertEqual(result.held_reasons, {"unowned Jellyfin episode in series root": 1})
            original_host_path = retention_seasons_live._host_path
            changed = False
            def concurrent_change(path, root_path):
                nonlocal changed
                if not changed:
                    changed = True
                    with sqlite3.connect(jellyfin) as db:
                        db.execute("UPDATE BaseItems SET IndexNumber=9 WHERE Id='season1'")
                return original_host_path(path, root_path)
            with patch.object(retention_seasons_live, '_host_path', side_effect=concurrent_change):
                with self.assertRaisesRegex(RuntimeError, "changed during season inventory"):
                    collect_season_paths(sonarr, jellyfin, data)
            with sqlite3.connect(jellyfin) as db:
                db.execute("UPDATE BaseItems SET IndexNumber=1 WHERE Id='season1'")
            with sqlite3.connect(jellyfin) as db:
                db.execute("UPDATE BaseItemProviders SET ProviderValue='999'")
            mismatched = collect_season_paths(sonarr, jellyfin, data)
            self.assertEqual(mismatched.exact_season_scopes, 1)
            self.assertEqual(mismatched.provider_certified_season_scopes, 0)
            self.assertEqual(mismatched.certified_scope_item_ids, {})
            with sqlite3.connect(jellyfin) as db:
                db.execute("UPDATE BaseItemProviders SET ProviderValue='101'")
                db.execute("UPDATE BaseItems SET IndexNumber=3 WHERE Id='season1'")
            wrong_season = collect_season_paths(sonarr, jellyfin, data)
            self.assertEqual(wrong_season.provider_certified_season_scopes, 0)
            with sqlite3.connect(jellyfin) as db:
                db.execute("UPDATE BaseItems SET IndexNumber=1 WHERE Id='season1'")
                db.execute("""INSERT INTO BaseItems VALUES
                    ('ep4','/media/other/stray.mkv',1,
                     'MediaBrowser.Controller.Entities.TV.Episode','series','season1',NULL)""")
            stray = collect_season_paths(sonarr, jellyfin, data)
            self.assertEqual(stray.exact_season_scopes, 1)
            self.assertEqual(stray.provider_certified_season_scopes, 0)
            self.assertEqual(stray.identity_held_reasons['unowned Jellyfin episode in provider season'], 2)
