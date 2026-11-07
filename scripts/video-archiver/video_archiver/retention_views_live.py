"""Read-only Jellyfin CollectionFolder proof for Archive view membership."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path, PurePosixPath

from .retention_years_live import _connect_readonly, _item_id


COLLECTION = "MediaBrowser.Controller.Entities.CollectionFolder"
MOVIE = "MediaBrowser.Controller.Entities.Movies.Movie"
SERIES = "MediaBrowser.Controller.Entities.TV.Series"
SEASON = "MediaBrowser.Controller.Entities.TV.Season"
EPISODE = "MediaBrowser.Controller.Entities.TV.Episode"


def archive_view_verified(jellyfin_db: Path, item_ids: tuple[str, ...], *,
                          kind: str) -> bool:
    """Require every item in exactly the intended Jellyfin Archive library."""
    if kind not in ("movie", "season") or not item_ids:
        raise ValueError("invalid Archive scope")
    normalized = tuple(_item_id(item) for item in item_ids)
    if len(set(normalized)) != len(normalized) or any(not item or item == "none"
                                                      for item in normalized):
        raise ValueError("duplicate or invalid Jellyfin item identity")
    expected_root = "Archive Movies" if kind == "movie" else "Archive TV"
    expected_types = {MOVIE} if kind == "movie" else {EPISODE, SEASON, SERIES}
    observed_types: set[str] = set()
    with closing(_connect_readonly(jellyfin_db)) as db:
        version = db.execute("PRAGMA data_version").fetchone()[0]
        for item in normalized:
            rows = db.execute(
                "SELECT Type FROM BaseItems WHERE replace(lower(Id),'-','')=?",
                (item,),
            ).fetchall()
            if len(rows) != 1 or rows[0][0] not in expected_types:
                return False
            observed_types.add(rows[0][0])
            ancestors = db.execute("""
                SELECT b.Path FROM AncestorIds a JOIN BaseItems b
                ON b.Id=a.ParentItemId
                WHERE replace(lower(a.ItemId),'-','')=? AND b.Type=?
            """, (item, COLLECTION)).fetchall()
            if len(ancestors) != 1 or not isinstance(ancestors[0][0], str):
                return False
            if PurePosixPath(ancestors[0][0]).name != expected_root:
                return False
        if db.execute("PRAGMA data_version").fetchone()[0] != version:
            raise RuntimeError("Jellyfin Archive membership changed during scan")
    return observed_types == expected_types if kind == "season" else True
