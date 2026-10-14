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
from recommendation_engine import rank_candidates, select_with_exposure_cooldown
from candidate_sources import (collect_listenbrainz_albums, collect_musicbrainz,
                               collect_openlibrary, collect_openlibrary_author,
                               collect_openlibrary_subject)
from trakt_oauth import refresh_access_token, write_secret
from trakt_sources import collect_trakt_recommendations

SNAPSHOT_PATH = Path(os.environ.get("PORTAL_SNAPSHOT_PATH", "/data/recommendations.json"))
LIBRARY_SNAPSHOT_PATH = os.environ.get("PORTAL_LIBRARY_SNAPSHOT_PATH")
HISTORY_SNAPSHOT_PATH = os.environ.get("PORTAL_HISTORY_SNAPSHOT_PATH")
REFRESH_TRIGGER_PATH = Path(os.environ.get("PORTAL_REFRESH_TRIGGER_PATH", "/data/refresh-now"))
SOURCE_STATUS_PATH = Path(os.environ.get("PORTAL_SOURCE_STATUS_PATH", "/data/source-status.json"))
REJECTED_PATH = Path(os.environ.get("PORTAL_REJECTED_PATH", "/data/rejected.json"))
EXPOSURE_PATH = Path(os.environ.get("PORTAL_EXPOSURE_PATH", "/data/exposure.json"))


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


def collect_tmdb_recommendations(library, history=(), rotation=0):
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
    tv_by_title = {}
    fallback_seeds = []
    for item in library:
        if not isinstance(item, dict):
            continue
        if item.get("authority") == "radarr" and item.get("media_type") == "movie":
            fallback_seeds.append(("movie", str(item.get("authority_id"))))
        elif item.get("authority") == "jellyfin" and item.get("media_type") == "tv":
            provider_ids = item.get("provider_ids") if isinstance(item.get("provider_ids"), dict) else {}
            tmdb_id = str(provider_ids.get("tmdb") or "")
            if tmdb_id.isdigit():
                fallback_seeds.append(("tv", tmdb_id))
                tv_by_title[str(item.get("title", "")).casefold().strip()] = tmdb_id
    recent_seeds = []
    for item in history:
        if not isinstance(item, dict):
            continue
        media_type = str(item.get("media_type", ""))
        tmdb_id = str(item.get("tmdb_id") or "")
        if media_type == "movie" and tmdb_id.isdigit():
            recent_seeds.append(("movie", tmdb_id))
        elif media_type in {"episode", "tv"}:
            series_tmdb = tv_by_title.get(str(item.get("series_title") or item.get("title") or "").casefold().strip())
            if series_tmdb:
                recent_seeds.append(("tv", series_tmdb))
    seeds.extend(recent_seeds)
    fallback_seeds = list(dict.fromkeys(fallback_seeds))
    if fallback_seeds:
        start = (max(0, int(rotation)) * 8) % len(fallback_seeds)
        seeds.extend(fallback_seeds[start:] + fallback_seeds[:start])
    unique_seeds = list(dict.fromkeys(
        (media_type, media_id) for media_type, media_id in seeds if media_id.isdigit()
    ))[:8]
    if not unique_seeds:
        return []
    cookie = seerr_session()
    results = []
    tv_detail_count = 0
    for media_type, media_id in unique_seeds:
        endpoint = f"/api/v1/{media_type}/{media_id}/recommendations"
        try:
            payload, _ = request_json(os.environ["SEERR_URL"] + endpoint,
                                      headers={"Cookie": cookie},
                                      timeout=int(os.environ.get("PORTAL_TMDB_TIMEOUT", "10")))
        except (OSError, TimeoutError, ValueError, urllib.error.URLError):
            continue
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
                try:
                    detail, _ = request_json(os.environ["SEERR_URL"] + f"/api/v1/tv/{item['id']}",
                                             headers={"Cookie": cookie},
                                             timeout=int(os.environ.get("PORTAL_TMDB_TIMEOUT", "10")))
                except (OSError, TimeoutError, ValueError, urllib.error.URLError):
                    continue
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


def collect_book_and_music_candidates(history=(), rotation=0):
    """Collect bounded, taste-driven non-video candidates with safe fallbacks."""
    results = []
    authors, subjects, artists = [], [], []
    for item in history:
        if not isinstance(item, dict):
            continue
        if item.get("authority") == "audiobookshelf":
            if item.get("author"):
                authors.append(str(item["author"]))
            subjects.extend(str(value) for value in item.get("genres", []) if value)
        if item.get("authority") == "jellyfin":
            if item.get("album_artist"):
                artists.append(str(item["album_artist"]))
            artists.extend(str(value) for value in item.get("artists", []) if value)
    authors = _rotated_unique(authors, rotation)
    subjects = _rotated_unique(subjects, rotation)
    artists = _rotated_unique(artists, rotation)
    for media_type in ("ebook", "audiobook"):
        before = len(results)
        for index, author in enumerate(authors[:2]):
            try:
                results.extend(collect_openlibrary_author(
                    author, media_type=media_type, request=request_json,
                    offset=((max(0, int(rotation)) + index) % 4) * 6))
            except (OSError, TimeoutError, ValueError, urllib.error.URLError):
                continue
        for index, subject in enumerate(subjects[:2]):
            try:
                results.extend(collect_openlibrary_subject(
                    subject, media_type=media_type, request=request_json,
                    offset=((max(0, int(rotation)) + index) % 4) * 6))
            except (OSError, TimeoutError, ValueError, urllib.error.URLError):
                continue
        if len(results) == before:
            variable = "PORTAL_BOOK_QUERIES" if media_type == "ebook" else "PORTAL_AUDIOBOOK_QUERIES"
            for query in _csv(variable, "")[:6]:
                try:
                    results.extend(collect_openlibrary(query, media_type=media_type, request=request_json))
                except (OSError, TimeoutError, ValueError, urllib.error.URLError):
                    continue
    music_before = len(results)
    for index, artist in enumerate(artists[:2]):
        try:
            results.extend(collect_listenbrainz_albums(
                artist, request=request_json, rotation=max(0, int(rotation)) + index))
        except (OSError, TimeoutError, ValueError, urllib.error.URLError):
            continue
    if len(results) == music_before:
        for query in _csv("PORTAL_MUSIC_MB_QUERIES", "")[:6]:
            try:
                results.extend(collect_musicbrainz(query, request=request_json))
            except (OSError, TimeoutError, ValueError, urllib.error.URLError):
                continue
    return results


def _rotated_unique(values, rotation):
    unique = list(dict.fromkeys(value.strip() for value in values if value and value.strip()))
    if not unique:
        return []
    start = max(0, int(rotation)) % len(unique)
    return unique[start:] + unique[:start]


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
    now = time.time()
    rotation = int(now // 86400)
    candidates = []
    for label, operation in (
        ("tmdb", lambda: collect_tmdb_recommendations(library, history, rotation)),
        ("lidarr", collect_lidarr),
        ("nonvideo", lambda: collect_book_and_music_candidates(history, rotation)),
    ):
        try:
            candidates.extend(operation())
        except (OSError, TimeoutError, KeyError, TypeError, ValueError, urllib.error.URLError) as exc:
            print(f"candidate_source_failed={label}:{type(exc).__name__}", flush=True)
    token_path = os.environ.get("TRAKT_ACCESS_TOKEN_PATH")
    client_id_path = os.environ.get("TRAKT_CLIENT_ID_PATH")
    refresh_path = os.environ.get("TRAKT_REFRESH_TOKEN_PATH")
    if token_path and client_id_path:
        try:
            def trakt_request(url, **kwargs):
                try:
                    return request_json(url, **kwargs)
                except urllib.error.HTTPError as error:
                    if error.code != 401 or not refresh_path:
                        raise
                    client_id = Path(client_id_path).read_text(encoding="utf-8").strip()
                    refresh_token = Path(refresh_path).read_text(encoding="utf-8").strip()
                    credentials = refresh_access_token(client_id=client_id, refresh_token=refresh_token)
                    write_secret(token_path, credentials["access_token"])
                    write_secret(refresh_path, credentials["refresh_token"])
                    headers = dict(kwargs.get("headers") or {})
                    headers["Authorization"] = "Bearer " + credentials["access_token"]
                    return request_json(url, **{**kwargs, "headers": headers})

            candidates.extend(collect_trakt_recommendations(
                request=trakt_request, access_token_path=token_path,
                client_id_path=client_id_path,
                limit=int(os.environ.get("PORTAL_TRAKT_LIMIT", "6"))))
        except (OSError, TimeoutError, ValueError, urllib.error.URLError):
            pass
    rejected = _read_rejected()
    candidates = [item for item in candidates if _candidate_key(item) not in rejected]
    ranked = _prepare_candidates(
        candidates,
        limit=200,
        library=library,
        history=history,
    )
    output, exposures = select_with_exposure_cooldown(
        ranked, exposures=_read_exposures(), now=now,
        cooldown_seconds=max(0, int(os.environ.get("PORTAL_EXPOSURE_COOLDOWN_SECONDS", "604800"))),
        retention_seconds=max(86400, int(os.environ.get("PORTAL_EXPOSURE_RETENTION_SECONDS", "2592000"))),
        per_media_limit=max(1, min(12, int(os.environ.get("PORTAL_MEDIA_TYPE_LIMIT", "8")))),
        limit=max(1, min(40, int(os.environ.get("PORTAL_RECOMMENDATION_LIMIT", "40")))),
    )
    output = _narrate(output)
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
    _write_exposures(exposures)
    labels = [str(item.get("source_label", "")) for item in candidates if isinstance(item, dict)]
    status = {
        "last_refresh": datetime_now(),
        "sources": {
            "Trakt": {"configured": bool(token_path and client_id_path),
                       "candidates": sum("Trakt" in label for label in labels)},
            "TMDB": {"configured": bool(os.environ.get("SEERR_URL")),
                     "candidates": sum("TMDB" in label for label in labels)},
            "Open Library": {"configured": True,
                              "candidates": sum("Open Library" in label for label in labels)},
            "MusicBrainz": {"configured": True,
                             "candidates": sum("MusicBrainz" in label for label in labels)},
            "ListenBrainz": {"configured": True,
                              "candidates": sum("ListenBrainz" in label for label in labels)},
            "Lidarr": {"configured": bool(os.environ.get("LIDARR_API_KEY_PATH")),
                       "candidates": sum("Lidarr" in label for label in labels)},
        },
    }
    SOURCE_STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")
    os.chmod(SOURCE_STATUS_PATH, 0o644)
    return output


def datetime_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_snapshot_items(path):
    """Read a sanitized auxiliary snapshot, failing closed when unavailable."""
    if not path:
        return ()
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return ()
    return value if isinstance(value, list) else ()


def _candidate_key(item):
    raw = "|".join(str(item.get(key, "")) for key in ("authority", "authority_id"))
    import hashlib
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _read_rejected():
    try:
        value = json.loads(REJECTED_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return set()
    return set(value) if isinstance(value, list) else set(value.keys()) if isinstance(value, dict) else set()


def _read_exposures():
    try:
        value = json.loads(EXPOSURE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_exposures(exposures):
    EXPOSURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=str(EXPOSURE_PATH.parent))
    os.close(fd)
    try:
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(exposures, handle, indent=2, sort_keys=True)
        os.chmod(temporary, 0o644)
        os.replace(temporary, EXPOSURE_PATH)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _refresh_library_snapshot():
    """Optionally write a separate sanitized ARR library snapshot.

    This is deliberately separate from recommendations until cross-authority
    identity matching has been validated. Missing configuration disables it.
    """
    if not LIBRARY_SNAPSHOT_PATH:
        return
    existing = _read_snapshot_items(LIBRARY_SNAPSHOT_PATH)
    libraries = []

    def add_source(authority, operation):
        try:
            values = operation()
            libraries.extend(item.__dict__ if hasattr(item, "__dict__") else dict(item)
                             for item in values)
        except (OSError, TimeoutError, KeyError, TypeError, ValueError, urllib.error.URLError) as exc:
            libraries.extend(item for item in existing
                             if isinstance(item, dict) and item.get("authority") == authority)
            print(f"library_source_failed={authority}:{type(exc).__name__}", flush=True)

    if os.environ.get("SONARR_API_KEY_PATH"):
        add_source("sonarr", lambda: collect_arr(
            os.environ.get("SONARR_URL", "http://192.168.20.40:8989"),
            os.environ["SONARR_API_KEY_PATH"], "sonarr", request=request_json))
    if os.environ.get("RADARR_API_KEY_PATH"):
        add_source("radarr", lambda: collect_arr(
            os.environ.get("RADARR_URL", "http://192.168.20.40:7878"),
            os.environ["RADARR_API_KEY_PATH"], "radarr", request=request_json))
    if os.environ.get("LIDARR_API_KEY_PATH"):
        add_source("lidarr", lambda: collect_lidarr_library(
            os.environ.get("LIDARR_URL", "http://192.168.20.40:8686"),
            os.environ["LIDARR_API_KEY_PATH"], request=request_json))
    if os.environ.get("JELLYFIN_API_KEY_PATH"):
        add_source("jellyfin", lambda: collect_jellyfin(
            os.environ.get("JELLYFIN_URL", "http://192.168.20.40:8096"),
            os.environ["JELLYFIN_API_KEY_PATH"], request=request_json))
    if os.environ.get("AUDIOBOOKSHELF_TOKEN_PATH"):
        library_ids = _csv("AUDIOBOOKSHELF_LIBRARY_IDS", "")
        if library_ids:
            add_source("audiobookshelf", lambda: collect_audiobookshelf(
                os.environ.get("AUDIOBOOKSHELF_URL", "http://192.168.20.40:30067"),
                os.environ["AUDIOBOOKSHELF_TOKEN_PATH"], request=request_json,
                library_ids=library_ids))
    if os.environ.get("LAZYLIBRARIAN_API_KEY_PATH"):
        add_source("lazylibrarian", lambda: collect_lazylibrarian(
            os.environ.get("LAZYLIBRARIAN_URL", "http://192.168.20.40:5299"),
            os.environ["LAZYLIBRARIAN_API_KEY_PATH"], request=request_json))
    target = Path(LIBRARY_SNAPSHOT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(libraries, handle, indent=2)
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
    existing = _read_snapshot_items(HISTORY_SNAPSHOT_PATH)
    history = []
    try:
        history.extend(collect_audiobookshelf_history(
            os.environ.get("AUDIOBOOKSHELF_URL", "http://192.168.20.40:30067"),
            os.environ["AUDIOBOOKSHELF_TOKEN_PATH"], user_id, request=request_json))
    except (OSError, TimeoutError, KeyError, TypeError, ValueError, urllib.error.URLError) as exc:
        history.extend(item for item in existing
                       if isinstance(item, dict) and item.get("authority") == "audiobookshelf")
        print(f"history_source_failed=audiobookshelf:{type(exc).__name__}", flush=True)
    jellyfin_user_id = os.environ.get("JELLYFIN_USER_ID")
    if jellyfin_user_id and os.environ.get("JELLYFIN_API_KEY_PATH"):
        try:
            history.extend(collect_jellyfin_history(
                os.environ.get("JELLYFIN_URL", "http://192.168.20.40:8096"),
                os.environ["JELLYFIN_API_KEY_PATH"], jellyfin_user_id,
                request=request_json))
        except (OSError, TimeoutError, KeyError, TypeError, ValueError, urllib.error.URLError) as exc:
            history.extend(item for item in existing
                           if isinstance(item, dict) and item.get("authority") == "jellyfin")
            print(f"history_source_failed=jellyfin:{type(exc).__name__}", flush=True)
    target = Path(HISTORY_SNAPSHOT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(history, handle, indent=2)
    os.chmod(temporary, 0o644)
    os.replace(temporary, target)


def refresh_due(interval, *, now=None):
    """Determine due-state from durable snapshot age, not process memory."""
    if REFRESH_TRIGGER_PATH.exists() or not SNAPSHOT_PATH.exists():
        return True
    timestamp = time.time() if now is None else float(now)
    try:
        age = max(0.0, timestamp - SNAPSHOT_PATH.stat().st_mtime)
    except OSError:
        return True
    return age >= max(1, int(interval))


def run_loop(interval, *, sleep=time.sleep):
    while True:
        if refresh_due(interval):
            try:
                if REFRESH_TRIGGER_PATH.exists():
                    REFRESH_TRIGGER_PATH.unlink(missing_ok=True)
                refresh_once()
            except Exception as exc:
                print(f"refresh_failed={type(exc).__name__}", flush=True)
        sleep(5)


if __name__ == "__main__":
    if os.environ.get("PORTAL_REFRESH_LOOP", "NO") == "YES":
        run_loop(int(os.environ.get("PORTAL_REFRESH_INTERVAL_SECONDS", "21600")))
    else:
        refresh_once()
