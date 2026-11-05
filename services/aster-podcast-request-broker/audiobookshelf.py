"""Read-only Audiobookshelf 2.36 podcast catalogue adapter."""

from __future__ import annotations

import json
from pathlib import Path
import stat
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from contract import ContractError, canonical_https_url, feed_sha256


class CatalogueError(RuntimeError):
    pass


class AudiobookshelfCatalogue:
    def __init__(self, base_url: str, key_path: Path, *, opener=urlopen):
        raw_base = base_url.rstrip("/")
        if raw_base == "http://unified-audiobookshelf-shadow":
            self.base_url = raw_base
        else:
            self.base_url = canonical_https_url(raw_base + "/", field="server-url").rstrip("/")
        info = key_path.lstat()
        if (not stat.S_ISREG(info.st_mode) or key_path.is_symlink() or info.st_nlink != 1
                or info.st_mode & 0o077 or not 32 <= info.st_size <= 4096):
            raise CatalogueError("api-key-custody")
        self.api_key = key_path.read_text().strip()
        if not 32 <= len(self.api_key) <= 4096 or any(char.isspace() for char in self.api_key):
            raise CatalogueError("api-key-schema")
        self.opener = opener

    def _get(self, path: str) -> object:
        request = Request(self.base_url + path, headers={
            "Authorization": "Bearer " + self.api_key,
            "Accept": "application/json",
            "User-Agent": "AsterPodcastRequestBroker/0.1",
        })
        with self.opener(request, timeout=20) as response:
            if response.status != 200 or int(response.headers.get("Content-Length", "0") or 0) > 2_000_000:
                raise CatalogueError("catalogue-http")
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise CatalogueError("catalogue-size")
        try:
            return json.loads(data)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CatalogueError("catalogue-json") from error

    def search(self, term: str, country: str) -> list[dict]:
        value = self._get("/api/search/podcast?" + urlencode({"term": term, "country": country}))
        if not isinstance(value, list) or len(value) > 200:
            raise CatalogueError("search-schema")
        output = []
        for item in value:
            if not isinstance(item, dict):
                continue
            artwork = item.get("cover")
            try:
                output.append({
                    "provider_id": str(item.get("id", "")),
                    "feed_url": item.get("feedUrl"),
                    "title": item.get("title"),
                    "artist": item.get("artistName") or "Unknown publisher",
                    "artwork_url": artwork if artwork else None,
                })
            except (TypeError, ValueError):
                continue
        return output

    def identities(self) -> tuple[set[str], set[str]]:
        value = self._get("/api/libraries")
        libraries = value.get("libraries") if isinstance(value, dict) else None
        podcasts = [item for item in libraries or []
                    if isinstance(item, dict) and item.get("mediaType") == "podcast"]
        if len(podcasts) != 1 or not isinstance(podcasts[0].get("id"), str):
            raise CatalogueError("podcast-library-cardinality")
        items = self._get("/api/libraries/" + quote(podcasts[0]["id"], safe="")
                          + "/items?limit=0&minified=0")
        results = items.get("results") if isinstance(items, dict) else None
        if not isinstance(results, list) or len(results) > 10_000:
            raise CatalogueError("podcast-items-schema")
        feed_hashes: set[str] = set()
        provider_ids: set[str] = set()
        for item in results:
            metadata = item.get("media", {}).get("metadata", {}) if isinstance(item, dict) else {}
            feed = metadata.get("feedUrl")
            provider = metadata.get("itunesId")
            if isinstance(feed, str) and feed:
                try:
                    feed_hashes.add(feed_sha256(canonical_https_url(feed, field="existing-feed")))
                except ContractError:
                    pass
            if isinstance(provider, (str, int)) and str(provider).isdigit():
                provider_ids.add(str(provider))
        return feed_hashes, provider_ids
