"""One-shot/looping read-only snapshot refresher for the shadow portal."""

from __future__ import annotations

import json
import os
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

SNAPSHOT_PATH = Path(os.environ.get("PORTAL_SNAPSHOT_PATH", "/data/recommendations.json"))


def request_json(url: str, *, method: str = "GET", body=None, headers=None):
    encoded = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    with urllib.request.urlopen(request, timeout=20) as response:
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


def refresh_once():
    candidates = collect_seerr() + collect_lidarr()
    unique = {}
    for candidate in candidates:
        unique.setdefault((candidate["authority"], candidate["authority_id"]), candidate)
    output = list(unique.values())[:20]
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


def _csv(name: str, default: str):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


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
