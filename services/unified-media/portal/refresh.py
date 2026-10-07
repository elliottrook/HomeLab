"""One-shot/looping read-only snapshot refresher for the shadow portal."""

from __future__ import annotations

import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from service_collectors import (
    collect_arr,
    collect_audiobookshelf,
    collect_audiobookshelf_history,
    collect_jellyfin,
    collect_jellyfin_history,
    collect_lazylibrarian,
    collect_lidarr as collect_lidarr_library,
)
from recommendation_engine import rank_candidates
from candidate_sources import collect_musicbrainz, collect_openlibrary

SNAPSHOT_PATH = Path(os.environ.get("PORTAL_SNAPSHOT_PATH", "/data/recommendations.json"))
LIBRARY_SNAPSHOT_PATH = os.environ.get("PORTAL_LIBRARY_SNAPSHOT_PATH")
HISTORY_SNAPSHOT_PATH = os.environ.get("PORTAL_HISTORY_SNAPSHOT_PATH")


def _narrate(candidates):
    """Add bounded local-AI explanations without making AI authoritative."""
    if os.environ.get("PORTAL_AI_ENABLED", "NO") != "YES":
        return candidates
    key_path = os.environ.get("ASTER_LLAMA_API_KEY_PATH")
    if not key_path:
        return candidates
    try:
        key = Path(key_path).read_text(encoding="utf-8").strip()
        if not key:
            return candidates
        ai_candidates = candidates[:min(8, int(os.environ.get("PORTAL_AI_MAX_ITEMS", "8")))]
        prompt_items = [{"index": index, "media_type": item["media_type"],
                         "title": item["title"], "reason": item["explanation"]}
                        for index, item in enumerate(ai_candidates)]
        body = {"model": os.environ.get("ASTER_MODEL", "local"),
                "messages": [{"role": "system", "content":
                              "Return only a JSON array of short explanations, one per input item, in order. "
                              "Do not invent facts, availability, ratings, or viewing history."},
                             {"role": "user", "content": json.dumps(prompt_items)}],
                "temperature": 0.2, "max_tokens": 480}
        payload, _ = request_json(
            os.environ.get("ASTER_LLAMA_URL", "http://192.168.70.12:11435/v1/chat/completions"),
            method="POST", body=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            timeout=90)
        content = payload["choices"][0]["message"]["content"]
        if os.environ.get("PORTAL_AI_DEBUG", "NO") == "YES":
            print(f"ai_narration_response={content[:300]!r}")
        explanations = json.loads(content)
        if not isinstance(explanations, list) or len(explanations) != len(prompt_items):
            return candidates
        output = [dict(item) for item in candidates]
        for index, explanation in enumerate(explanations):
            if isinstance(explanation, str) and 1 <= len(explanation) <= 280:
                output[index]["explanation"] = explanation
        return output
    except (OSError, KeyError, TypeError, ValueError, IndexError, urllib.error.URLError) as exc:
        if os.environ.get("PORTAL_AI_DEBUG", "NO") == "YES":
            print(f"ai_narration_failed={type(exc).__name__}")
        return candidates


def request_json(url: str, *, method: str = "GET", body=None, headers=None,
                 params=None, timeout: int = 20):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    encoded = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read() or b"{}"), dict(response.headers)


def seerr_session():
    password = Path(os.environ["SEERR_PASSWORD_PATH"]).read_text(encoding="utf-8").strip()
    _, headers = request_json(
        os.environ["SEERR_URL"] + "/api/v1/auth/local", method="POST",
        body={"email": os.environ["SEERR_EMAIL"], "password": password},
        headers={"Content-Type": "application/json"},
    )
    cookie = headers.get("Set-Cookie", "").split(";", 1)[0]
    if not cookie:
        raise RuntimeError("Seerr returned no session cookie")
    return cookie


def collect_tmdb_recommendations(library):
    """Collect TMDB per-title recommendations through Seerr's TMDB proxy.

    Seerr remains the request authority, but its generic discovery feed is not
    used. Seeds are bounded to existing Radarr/Sonarr identities so TMDB's
    recommendations are grounded in this library rather than a generic chart.
    """
    seeds = []
    configured = _csv("PORTAL_TMDB_SEEDS", "")
    for value in configured[:6]:
        media_type, separator, media_id = value.partition(":")
        if separator and media_type in {"movie", "tv"} and media_id.isdigit():
            seeds.append((media_type, media_id))
    for item in library:
        if not isinstance(item, dict):
            continue
        if item.get("authority") == "radarr" and item.get("media_type") == "movie":
            seeds.append(("movie", str(item.get("authority_id"))))
        elif item.get("authority") == "sonarr" and item.get("media_type") == "tv":
            seeds.append(("tv", str(item.get("authority_id"))))
    unique_seeds = list(dict.fromkeys(
        (media_type, media_id) for media_type, media_id in seeds if media_id.isdigit()
    ))[:4]
    if not unique_seeds:
        return []
    cookie = seerr_session()
    results = []
    tv_detail_count = 0
    for media_type, media_id in unique_seeds:
        endpoint = f"/api/v1/{media_type}/{media_id}/recommendations"
        payload, _ = request_json(os.environ["SEERR_URL"] + endpoint,
                                  headers={"Cookie": cookie})
        for item in payload.get("results", [])[:4]:
            if item.get("mediaInfo"):
                continue
            title = item.get("title") or item.get("name")
            if not item.get("id") or not title:
                continue
            candidate = _seerr_candidate(item, media_type, "TMDB per-title recommendations")
            if media_type == "tv":
                if tv_detail_count >= 8:
                    continue
                tv_detail_count += 1
                detail, _ = request_json(os.environ["SEERR_URL"] + f"/api/v1/tv/{item['id']}",
                                         headers={"Cookie": cookie})
                seasons = [season.get("seasonNumber") for season in detail.get("seasons", [])
                           if isinstance(season, dict) and isinstance(season.get("seasonNumber"), int)
                           and season.get("seasonNumber") > 0]
                if not seasons:
                    continue
                candidate["seasons"] = seasons
            results.append(candidate)
    return results


_TMDB_GENRES = {
    12: "Adventure", 14: "Fantasy", 16: "Animation", 18: "Drama", 27: "Horror",
    28: "Action", 35: "Comedy", 36: "History", 37: "Western", 53: "Thriller",
    80: "Crime", 99: "Documentary", 878: "Science Fiction", 9648: "Mystery",
    10402: "Music", 10749: "Romance", 10751: "Family", 10752: "War", 10759: "Action & Adventure",
    10762: "Kids", 10763: "News", 10764: "Reality", 10765: "Sci-Fi & Fantasy",
    10766: "Soap", 10767: "Talk", 10768: "War & Politics",
}


def _seerr_candidate(item, media_type, source_label):
    genre_ids = item.get("genreIds") if isinstance(item.get("genreIds"), list) else []
    genres = [_TMDB_GENRES[value] for value in genre_ids if value in _TMDB_GENRES]
    return {"media_type": media_type, "authority": "seerr",
            "authority_id": str(item["id"]),
            "title": item.get("title") or item.get("name"),
            "score": float(item.get("voteAverage") or 0.0),
            "overview": item.get("overview") or "",
            "poster_path": item.get("posterPath") or "",
            "backdrop_path": item.get("backdropPath") or "",
            "year": str(item.get("releaseDate") or item.get("firstAirDate") or "")[:4],
            "rating": item.get("voteAverage"), "genres": genres,
            "source_label": source_label,
            "explanation": f"Popular {media_type} discovery result not currently managed or requested."}


def collect_lidarr():
    key = Path(os.environ["LIDARR_API_KEY_PATH"]).read_text(encoding="utf-8").strip()
    headers = {"X-Api-Key": key}
    results = []
    for query in _csv("PORTAL_LIDARR_QUERIES", "Miles Davis|Kind of Blue,The Beatles|Abbey Road"):
        artist_query, separator, album_query = query.partition("|")
        if not separator:
            # Legacy title-only configuration is intentionally fail-closed.
            # A title is not enough to identify a safe music acquisition.
            continue
        payload, _ = request_json(
            os.environ["LIDARR_URL"] + "/api/v1/album/lookup?" + urllib.parse.urlencode({"term": f"{artist_query} {album_query}"}),
            headers=headers,
        )
        item = _unique_exact_album(payload, artist_query, album_query)
        if item is None:
            continue
        album_id = item.get("foreignAlbumId")
        if not album_id:
            continue
        existing, _ = request_json(
            os.environ["LIDARR_URL"] + "/api/v1/album?" + urllib.parse.urlencode({"foreignAlbumId": album_id}),
            headers=headers,
        )
        if existing:
            continue
        artist = (item.get("artist") or {}).get("artistName", "")
        results.append({"media_type": "album", "authority": "lidarr",
                        "authority_id": str(album_id), "title": item["title"],
                        "score": 0.65,
                        "explanation": "Unmanaged album from the Lidarr catalog" +
                        (f" by {artist}." if artist else ".")})
    return results


def collect_book_and_music_candidates():
    """Collect bounded non-video candidates from explicit seed configuration."""
    results = []
    for query in _csv("PORTAL_BOOK_QUERIES", "")[:6]:
        try:
            results.extend(collect_openlibrary(query, media_type="ebook", request=request_json))
        except (OSError, TimeoutError, ValueError, urllib.error.URLError):
            continue
    for query in _csv("PORTAL_AUDIOBOOK_QUERIES", "")[:6]:
        try:
            results.extend(collect_openlibrary(query, media_type="audiobook", request=request_json))
        except (OSError, TimeoutError, ValueError, urllib.error.URLError):
            continue
    for query in _csv("PORTAL_MUSIC_MB_QUERIES", "")[:6]:
        try:
            results.extend(collect_musicbrainz(query, request=request_json))
        except (OSError, TimeoutError, ValueError, urllib.error.URLError):
            continue
    return results


def _unique_exact_album(items, artist_query, album_query):
    matches = [item for item in items
               if item.get("title", "").casefold() == album_query.casefold()
               and (item.get("artist") or {}).get("artistName", "").casefold()
               == artist_query.casefold()]
    return matches[0] if len(matches) == 1 else None


def _prepare_candidates(candidates, limit=20, *, library=(), history=()):
    """Rank provider candidates through the shared fail-closed engine."""
    return rank_candidates(candidates, library=library, history=history, limit=limit)


def refresh_once():
    _refresh_library_snapshot()
    _refresh_history_snapshot()
    library = _read_snapshot_items(LIBRARY_SNAPSHOT_PATH)
    history = _read_snapshot_items(HISTORY_SNAPSHOT_PATH)
    candidates = (collect_tmdb_recommendations(library) + collect_lidarr() +
                  collect_book_and_music_candidates())
    output = _narrate(_prepare_candidates(
        candidates,
        limit=max(1, min(40, int(os.environ.get("PORTAL_RECOMMENDATION_LIMIT", "40")))),
        library=library,
        history=history,
    ))
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=str(SNAPSHOT_PATH.parent))
    os.close(fd)
    try:
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(output, handle, indent=2)
        os.chmod(temporary, 0o644)
        os.replace(temporary, SNAPSHOT_PATH)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return output


def _read_snapshot_items(path):
    """Read a sanitized auxiliary snapshot, failing closed when unavailable."""
    if not path:
        return ()
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return ()
    return value if isinstance(value, list) else ()


def _refresh_library_snapshot():
    """Optionally write a separate sanitized ARR library snapshot.

    This is deliberately separate from recommendations until cross-authority
    identity matching has been validated. Missing configuration disables it.
    """
    if not LIBRARY_SNAPSHOT_PATH:
        return
    libraries = []
    if os.environ.get("SONARR_API_KEY_PATH"):
        libraries.extend(collect_arr(
            os.environ.get("SONARR_URL", "http://192.168.20.40:8989"),
            os.environ["SONARR_API_KEY_PATH"], "sonarr", request=request_json))
    if os.environ.get("RADARR_API_KEY_PATH"):
        libraries.extend(collect_arr(
            os.environ.get("RADARR_URL", "http://192.168.20.40:7878"),
            os.environ["RADARR_API_KEY_PATH"], "radarr", request=request_json))
    if os.environ.get("LIDARR_API_KEY_PATH"):
        libraries.extend(collect_lidarr_library(
            os.environ.get("LIDARR_URL", "http://192.168.20.40:8686"),
            os.environ["LIDARR_API_KEY_PATH"], request=request_json))
    if os.environ.get("JELLYFIN_API_KEY_PATH"):
        libraries.extend(collect_jellyfin(
            os.environ.get("JELLYFIN_URL", "http://192.168.20.40:8096"),
            os.environ["JELLYFIN_API_KEY_PATH"], request=request_json))
    if os.environ.get("AUDIOBOOKSHELF_TOKEN_PATH"):
        library_ids = _csv("AUDIOBOOKSHELF_LIBRARY_IDS", "")
        if library_ids:
            libraries.extend(collect_audiobookshelf(
                os.environ.get("AUDIOBOOKSHELF_URL", "http://192.168.20.40:30067"),
                os.environ["AUDIOBOOKSHELF_TOKEN_PATH"], request=request_json,
                library_ids=library_ids))
    if os.environ.get("LAZYLIBRARIAN_API_KEY_PATH"):
        libraries.extend(collect_lazylibrarian(
            os.environ.get("LAZYLIBRARIAN_URL", "http://192.168.20.40:5299"),
            os.environ["LAZYLIBRARIAN_API_KEY_PATH"], request=request_json))
    target = Path(LIBRARY_SNAPSHOT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump([item.__dict__ for item in libraries], handle, indent=2)
    os.chmod(temporary, 0o644)
    os.replace(temporary, target)


def _csv(name: str, default: str):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


def _refresh_history_snapshot():
    """Write a separate sanitized history snapshot when explicitly configured."""
    if not HISTORY_SNAPSHOT_PATH or not os.environ.get("AUDIOBOOKSHELF_TOKEN_PATH"):
        return
    user_id = os.environ.get("AUDIOBOOKSHELF_USER_ID")
    if not user_id:
        return
    history = list(collect_audiobookshelf_history(
        os.environ.get("AUDIOBOOKSHELF_URL", "http://192.168.20.40:30067"),
        os.environ["AUDIOBOOKSHELF_TOKEN_PATH"], user_id, request=request_json))
    jellyfin_user_id = os.environ.get("JELLYFIN_USER_ID")
    if jellyfin_user_id and os.environ.get("JELLYFIN_API_KEY_PATH"):
        history.extend(collect_jellyfin_history(
            os.environ.get("JELLYFIN_URL", "http://192.168.20.40:8096"),
            os.environ["JELLYFIN_API_KEY_PATH"], jellyfin_user_id,
            request=request_json))
    target = Path(HISTORY_SNAPSHOT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(history, handle, indent=2)
    os.chmod(temporary, 0o644)
    os.replace(temporary, target)


if __name__ == "__main__":
    if os.environ.get("PORTAL_REFRESH_LOOP", "NO") == "YES":
        interval = int(os.environ.get("PORTAL_REFRESH_INTERVAL_SECONDS", "21600"))
        while True:
            try:
                refresh_once()
            except Exception as exc:
                print(f"refresh_failed={type(exc).__name__}")
            time.sleep(interval)
    else:
        refresh_once()
