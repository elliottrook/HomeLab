#!/usr/bin/env python3
"""Loopback-only token-hiding art and playback proxy."""

import http.server
import json
import threading
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

import xbmc

from core import GuestCatalogueError, item_id, proxy_target, validate_hls_route


HOST = "127.0.0.1"
PORT = 57321
PROXY_URL = "http://127.0.0.1:" + str(PORT)
CREDENTIAL = Path("/storage/.aster-private/jellyfin-guest.json")


def credential():
    details = CREDENTIAL.stat()
    if details.st_mode & 0o077:
        raise GuestCatalogueError("credential-permissions")
    value = json.loads(CREDENTIAL.read_text(encoding="utf-8"))
    if value.get("schema") != 1 or not value.get("access_token"):
        raise GuestCatalogueError("credential-schema")
    return value


class Handler(http.server.BaseHTTPRequestHandler):
    # Jellyfin's live transcode has no stable Content-Length. HTTP/1.0 gives
    # Kodi unambiguous connection-close framing without exposing a token URL.
    protocol_version = "HTTP/1.0"

    def log_message(self, _format, *_arguments):
        return

    def do_HEAD(self):
        self._proxy(False)

    def do_GET(self):
        self._proxy(True)

    def _proxy(self, include_body):
        try:
            raw_path, _separator, raw_query = self.path.partition("?")
            path = raw_path.strip("/").split("/")
            auth = credential()
            authorization = (
                "MediaBrowser Client=AsterTV Guest, Device=AsterTV-Jen, "
                "DeviceId=" + auth["device_id"] + ", Version=1, Token="
                + auth["access_token"]
            )
            headers = {"X-Emby-Token": auth["access_token"],
                       "Authorization": authorization}
            if len(path) == 2 and path[0] == "art":
                target = auth["server_url"].rstrip("/") + proxy_target("art", path[1])
                self._relay(target, headers, include_body)
                return
            if (len(path) == 3 and path[0] == "stream"
                    and path[2] == "master.m3u8"):
                self._master(auth, headers, item_id(path[1]), include_body)
                return
            if len(path) >= 3 and path[0] == "hls":
                identifier = item_id(path[1])
                resource = "/".join(path[2:])
                target = (auth["server_url"].rstrip("/") + "/Videos/" + identifier
                          + "/" + validate_hls_route(resource, raw_query))
                if resource.endswith(".m3u8"):
                    self._playlist(target, headers, identifier, include_body)
                else:
                    self._relay(target, headers, include_body)
                return
            raise GuestCatalogueError("proxy-path-denied")

        except (GuestCatalogueError, OSError, ValueError, KeyError,
                urllib.error.URLError):
            try:
                self.send_error(404)
            except (BrokenPipeError, ConnectionResetError):
                return

    def _open(self, target, headers, include_body=True):
        request = urllib.request.Request(target, method="GET" if include_body else "HEAD",
                                         headers=headers)
        return urllib.request.urlopen(request, timeout=30)

    def _relay(self, target, headers, include_body):
        with self._open(target, headers, include_body) as response:
            self.send_response(response.status)
            for header in ("Content-Type", "Content-Length", "Accept-Ranges",
                           "Content-Range", "Cache-Control"):
                if response.headers.get(header):
                    self.send_header(header, response.headers[header])
            self.end_headers()
            if include_body:
                while True:
                    block = response.read(256 * 1024)
                    if not block:
                        break
                    try:
                        self.wfile.write(block)
                    except (BrokenPipeError, ConnectionResetError):
                        return

    def _json(self, target, headers):
        with self._open(target, headers) as response:
            return json.load(response)

    def _master(self, auth, headers, identifier, include_body):
        info = self._json(
            auth["server_url"].rstrip("/") + "/Items/" + identifier
            + "/PlaybackInfo?" + urllib.parse.urlencode({"UserId": auth["user_id"]}),
            headers,
        )
        sources = info.get("MediaSources") or []
        if len(sources) != 1 or not info.get("PlaySessionId"):
            raise GuestCatalogueError("playback-info-schema")
        source = sources[0]; streams = source.get("MediaStreams") or []
        video = next(row for row in streams if row.get("Type") == "Video")
        audio = next(row for row in streams if row.get("Type") == "Audio")
        query = urllib.parse.urlencode({
            "MediaSourceId": source["Id"], "PlaySessionId": info["PlaySessionId"],
            "VideoStreamIndex": video["Index"], "AudioStreamIndex": audio["Index"],
            "VideoCodec": "h264", "AudioCodec": "aac", "MaxWidth": 1920,
            "VideoBitrate": 16000000, "AudioBitrate": 192000,
            "TranscodingMaxAudioChannels": 2, "SegmentContainer": "ts",
            "MinSegments": 2, "BreakOnNonKeyFrames": "true",
            "TranscodingProtocol": "hls",
        })
        target = (auth["server_url"].rstrip("/") + "/Videos/" + identifier
                  + "/master.m3u8?" + query)
        self._playlist(target, headers, identifier, include_body, master=True)

    def _playlist(self, target, headers, identifier, include_body, master=False):
        if not include_body:
            payload = b""
        else:
            with self._open(target, headers) as response:
                lines = response.read(4 * 1024 * 1024 + 1).decode().splitlines()
            if sum(len(line) + 1 for line in lines) > 4 * 1024 * 1024:
                raise GuestCatalogueError("playlist-too-large")
            rewritten = []
            for line in lines:
                if line.startswith("#EXT-X-IMAGE-STREAM-INF"):
                    continue
                if line.startswith("#") or not line:
                    rewritten.append(line)
                    continue
                resource, separator, query = line.partition("?")
                safe = validate_hls_route(resource, query)
                rewritten.append(PROXY_URL + "/hls/" + identifier + "/" + safe)
            payload = ("\n".join(rewritten) + "\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.apple.mpegurl")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store" if master else "private, max-age=5")
        self.end_headers()
        if include_body:
            self.wfile.write(payload)


server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
monitor = xbmc.Monitor()
while not monitor.waitForAbort(0.5):
    pass
server.shutdown()
server.server_close()
