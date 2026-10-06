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
    collect_lazylibrarian,
    collect_lidarr as collect_lidarr_library,
)

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


def collect_seerr():
    cookie = seerr_session()
    results = []
    for query in _csv("PORTAL_SEERR_QUERIES", "Arrival,Dune"):
        payload, _ = request_json(
            os.environ["SEERR_URL"] + "/api/v1/search?" + urllib.parse.urlencode({"query": query}),
            headers={"Cookie": cookie},
        )
        for item in payload.get("results", []):
            if item.get("mediaType") != "movie" or item.get("mediaInfo"):
                continue
            if not item.get("id") or not item.get("title"):
                continue
            results.append({"media_type": "movie", "authority": "seerr",
                            "authority_id": str(item["id"]), "title": item["title"],
                            "score": 0.70,
                            "explanation": "Unrequested movie from the Seerr catalog."})
    return results


def collect_lidarr():
    key = Path(os.environ["LIDARR_API_KEY_PATH"]).read_text(encoding="utf-8").strip()
    headers = {"X-Api-Key": key}
    results = []
    for query in _csv("PORTAL_LIDARR_QUERIES", "Kind of Blue,Bitches Brew"):
        payload, _ = request_json(
            os.environ["LIDARR_URL"] + "/api/v1/album/lookup?" + urllib.parse.urlencode({"term": query}),
            headers=headers,
        )
        for item in payload:
            album_id = item.get("foreignAlbumId")
            if not album_id or not item.get("title"):
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
            break
    return results


def _prepare_candidates(candidates, limit=20):
    """Deduplicate by title identity and fail closed on collisions."""
    by_identity = {}
    for candidate in candidates:
        key = (candidate["authority"], candidate["media_type"], candidate["title"].casefold())
        existing = by_identity.get(key)
        if existing is None:
            by_identity[key] = dict(candidate, match_count=1)
        else:
            existing["match_count"] = existing.get("match_count", 1) + 1
    safe = [item for item in by_identity.values()
            if item.get("match_count") == 1 and not item.get("owned") and not item.get("archived")]
    safe.sort(key=lambda item: (-item.get("score", 0), item["media_type"],
                               item["title"].casefold(), item["authority_id"]))
    return safe[:max(0, limit)]


def refresh_once():
    candidates = collect_seerr() + collect_lidarr()
    output = _narrate(_prepare_candidates(candidates))
    _refresh_library_snapshot()
    _refresh_history_snapshot()
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
    history = collect_audiobookshelf_history(
        os.environ.get("AUDIOBOOKSHELF_URL", "http://192.168.20.40:30067"),
        os.environ["AUDIOBOOKSHELF_TOKEN_PATH"], user_id, request=request_json)
    target = Path(HISTORY_SNAPSHOT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(list(history), handle, indent=2)
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
