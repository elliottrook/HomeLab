"""Minimal read-only Lidarr REST client using only the standard library."""
import json
import urllib.request
import urllib.error


class LidarrError(Exception):
    pass


class LidarrClient:
    def __init__(self, base_url, api_key, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _get(self, path):
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method="GET")
        req.add_header("X-Api-Key", self.api_key)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            raise LidarrError(f"GET {path} -> HTTP {e.code}: {e.read()[:500]}") from e
        except urllib.error.URLError as e:
            raise LidarrError(f"GET {path} -> unreachable: {e.reason}") from e

    def get_artist_names(self):
        """Return the set of managed artist names (folderName basis)."""
        artists = self._get("/api/v1/artist")
        return {a["artistName"] for a in artists}
