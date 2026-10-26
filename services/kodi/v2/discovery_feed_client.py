"""Authenticated, fail-closed Acquisition Hub discovery reader and cache."""

import os
from pathlib import Path
import urllib.error
import urllib.request

from landing_recommendations import MAX_BYTES, parse_feed


class DiscoveryUnavailable(RuntimeError):
    pass


def require(value, code):
    if not value:
        raise DiscoveryUnavailable(code)


def _atomic(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with open(temporary, "wb") as output:
        os.fchmod(output.fileno(), 0o600)
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)


class DiscoveryFeedClient:
    def __init__(self, base, token_path, cache_root,
                 opener=urllib.request.urlopen):
        require(base == "http://192.168.20.40:8788",
                "discovery-client-broker-invalid")
        self.base = base
        self.token_path = Path(token_path)
        self.cache_root = Path(cache_root)
        self.opener = opener

    def _cache(self, domain):
        require(domain in ("media", "music", "books"),
                "discovery-client-domain-invalid")
        return self.cache_root / (domain + ".json")

    def _read_token(self):
        try:
            token = self.token_path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError) as error:
            raise DiscoveryUnavailable("discovery-client-token-unavailable") from error
        require(32 <= len(token) <= 512 and "\n" not in token,
                "discovery-client-token-invalid")
        return token

    def _remote(self, domain):
        token = self._read_token()
        request = urllib.request.Request(
            self.base + "/v1/discovery/" + domain,
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/json"},
            method="GET",
        )
        try:
            with self.opener(request, timeout=10) as response:
                raw = response.read(MAX_BYTES + 1)
                require(response.status == 200 and 0 < len(raw) <= MAX_BYTES,
                        "discovery-client-response-invalid")
                return raw
        except DiscoveryUnavailable:
            raise
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as error:
            raise DiscoveryUnavailable("discovery-client-unavailable") from error

    def load(self, domain, now):
        cache = self._cache(domain)
        try:
            raw = self._remote(domain)
            parsed = parse_feed(raw, domain, now)
            _atomic(cache, raw)
            return parsed, "live"
        except (DiscoveryUnavailable, ValueError, OSError):
            try:
                raw = cache.read_bytes()
                require(0 < len(raw) <= MAX_BYTES, "discovery-client-cache-invalid")
                return parse_feed(raw, domain, now), "cache"
            except (OSError, ValueError, DiscoveryUnavailable) as error:
                raise DiscoveryUnavailable("discovery-client-feed-unavailable") from error
