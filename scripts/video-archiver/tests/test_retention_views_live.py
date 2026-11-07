"""Archive membership is a Jellyfin library fact, not a file-path guess."""

import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase

from video_archiver.retention_views_live import archive_view_verified


class ArchiveViewTests(TestCase):
    def test_requires_one_matching_collection_folder_per_item(self):
        with tempfile.TemporaryDirectory() as temp:
            db_path = Path(temp) / "jellyfin.db"
            with sqlite3.connect(db_path) as db:
                db.executescript("""
                    CREATE TABLE BaseItems(Id TEXT, Type TEXT, Path TEXT);
                    CREATE TABLE AncestorIds(ItemId TEXT, ParentItemId TEXT);
                    INSERT INTO BaseItems VALUES
                      ('library-m','MediaBrowser.Controller.Entities.CollectionFolder','/config/root/Archive Movies'),
                      ('library-t','MediaBrowser.Controller.Entities.CollectionFolder','/config/root/Archive TV'),
                      ('film','MediaBrowser.Controller.Entities.Movies.Movie','/media/archive-movies/film.mkv'),
                      ('series','MediaBrowser.Controller.Entities.TV.Series',NULL),
                      ('season','MediaBrowser.Controller.Entities.TV.Season',NULL),
                      ('episode','MediaBrowser.Controller.Entities.TV.Episode','/media/archive-tv/episode.mkv');
                    INSERT INTO AncestorIds VALUES
                      ('film','library-m'),('series','library-t'),
                      ('season','library-t'),('episode','library-t');
                """)
            self.assertTrue(archive_view_verified(db_path, ("film",), kind="movie"))
            with sqlite3.connect(db_path) as db:
                db.execute("INSERT INTO BaseItems VALUES (?,?,?)", (
                    '11111111-1111-1111-1111-111111111111',
                    'MediaBrowser.Controller.Entities.Movies.Movie',
                    '/media/archive-movies/other.mkv',
                ))
                db.execute("INSERT INTO AncestorIds VALUES (?,?)", (
                    '11111111-1111-1111-1111-111111111111', 'library-m',
                ))
            self.assertTrue(archive_view_verified(
                db_path, ('11111111111111111111111111111111',), kind="movie"))
            self.assertTrue(archive_view_verified(
                db_path, ("episode", "season", "series"), kind="season"))
            with sqlite3.connect(db_path) as db:
                db.execute("INSERT INTO AncestorIds VALUES ('film','library-t')")
            self.assertFalse(archive_view_verified(db_path, ("film",), kind="movie"))
            with sqlite3.connect(db_path) as db:
                db.execute("DELETE FROM AncestorIds WHERE ItemId='film' AND ParentItemId='library-t'")
                db.execute("DELETE FROM AncestorIds WHERE ItemId='episode'")
            self.assertFalse(archive_view_verified(
                db_path, ("episode", "season", "series"), kind="season"))
