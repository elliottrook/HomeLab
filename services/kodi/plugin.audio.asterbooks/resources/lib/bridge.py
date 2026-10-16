"""Loopback-only Audiobookshelf audio bridge; no Kodi imports or token URLs.

The UNIX control socket is private to the Kodi profile user. It resolves a
catalogue ID to verified ABS file inodes and issues random, process-local
capabilities. HTTP GET/HEAD on loopback forwards byte ranges with bearer auth
in an upstream header. A proxy URL is never a reusable ABS credential.
"""

import http.server
import json
import math
import os
import re
import secrets
import socket
import socketserver
import stat
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


ID = re.compile(r'[A-Za-z0-9_-]{1,128}\Z')
INO = re.compile(r'[0-9]{1,24}\Z')
RANGE = re.compile(r'bytes=(?:[0-9]+-[0-9]*|-[0-9]+)\Z')
CAP = re.compile(r'/audio/([A-Za-z0-9_-]{32,64})\Z')
MAX_METADATA = 1024 * 1024
MAX_CONTROL = 4096
TTL = 12 * 3600
CONTROL_SOCKET = 'b.sock'  # Keep the full path below macOS's UNIX socket limit.


class BridgeError(Exception):
    """Safe, non-secret bridge failure."""


def finite_seconds(value):
    """Accept only bounded numeric timeline values, never booleans or NaN."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value < 0 or value > 7 * 24 * 3600:
        return None
    return float(value)


def chapter_starts(media, files):
    """Map global ABS chapter times to verified file indices and local offsets.

    A single audio file needs no track map. For multiple files the ABS tracks
    must align with audioFiles in order; otherwise file parts remain available.
    """
    chapters = media.get('chapters') or []
    if not isinstance(chapters, list) or not 0 < len(chapters) <= 500 or not files:
        return []
    if len(files) == 1:
        spans = [(0.0, finite_seconds(files[0].get('duration')))]
    else:
        tracks = media.get('tracks') or []
        if not isinstance(tracks, list) or len(tracks) != len(files):
            return []
        spans = []
        for file, track in zip(files, tracks):
            if not isinstance(track, dict):
                return []
            start = finite_seconds(track.get('startOffset'))
            duration = finite_seconds(track.get('duration'))
            if start is None or duration is None or duration <= 0:
                return []
            file_duration = finite_seconds(file.get('duration'))
            if file_duration is not None and abs(file_duration - duration) > 1:
                return []
            spans.append((start, duration))
        if spans[0][0] != 0 or any(abs(spans[n][0] - (spans[n-1][0] + spans[n-1][1])) > 1
                                     for n in range(1, len(spans))):
            return []
    result = []
    for number, chapter in enumerate(chapters, 1):
        if not isinstance(chapter, dict):
            continue
        start = finite_seconds(chapter.get('start'))
        end = finite_seconds(chapter.get('end'))
        if start is None or end is None or end <= start:
            continue
        for index, (file_start, duration) in enumerate(spans):
            if start >= file_start and (duration is None or start < file_start + duration):
                title = chapter.get('title')
                if not isinstance(title, str) or not title.strip():
                    title = 'Chapter ' + str(number)
                result.append((title.strip()[:160], index, start - file_start, end - start, number))
                break
    return result


def load_config(path):
    """Require a private regular file and a TLS-only upstream endpoint."""
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_size > 8192:
        raise BridgeError('Config must be a private, small regular file (mode 0600).')
    config = json.loads(path.read_text(encoding='utf-8'))
    url = config.get('server_url', '').rstrip('/')
    parts = urlsplit(url)
    if (parts.scheme != 'https' or not parts.hostname or parts.username or
            parts.password or parts.path or parts.query or parts.fragment):
        raise BridgeError('Audiobookshelf server_url must be a bare HTTPS origin.')
    key = config.get('api_key', '')
    if not isinstance(key, str) or not 16 <= len(key) <= 4096 or any(c.isspace() for c in key):
        raise BridgeError('A dedicated Audiobookshelf API key is required.')
    return url, key


def secure_kodi_log(path):
    """Keep temporary local playback capabilities out of other users' logs."""
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise BridgeError('Kodi log is not a regular file owned by this user.')
        os.fchmod(fd, 0o600)
    finally:
        os.close(fd)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise BridgeError('Audiobookshelf redirected the private request.')


class Bridge:
    def __init__(self, server_url, api_key, opener=None, clock=None):
        self.server_url = server_url
        self.api_key = api_key
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self.clock = clock or time.time
        self.capabilities = {}
        self.lock = threading.Lock()
        self.http = None
        self.control = None
        self.http_started = False
        self.control_started = False

    def upstream(self, path, byte_range=None, method='GET'):
        headers = {'Authorization': 'Bearer ' + self.api_key}
        if byte_range:
            headers['Range'] = byte_range
        request = urllib.request.Request(self.server_url + path, headers=headers, method=method)
        return self.opener.open(request, timeout=15)

    def metadata(self, item_id):
        if not ID.fullmatch(item_id):
            raise BridgeError('Invalid catalogue ID.')
        try:
            with self.upstream('/api/items/' + item_id + '?expanded=1') as response:
                if response.status != 200:
                    raise BridgeError('Audiobookshelf metadata unavailable.')
                raw = response.read(MAX_METADATA + 1)
            if len(raw) > MAX_METADATA:
                raise BridgeError('Audiobookshelf metadata exceeds the local limit.')
            item = json.loads(raw)
            if not isinstance(item, dict):
                raise ValueError('Invalid metadata shape')
            return item
        except (urllib.error.URLError, ValueError, OSError, BridgeError) as exc:
            raise BridgeError('Audiobookshelf metadata unavailable.') from exc

    def describe(self, kind, item_id):
        if kind not in ('audiobook', 'podcast'):
            raise BridgeError('Unknown audio kind.')
        item = self.metadata(item_id)
        if item.get('id') != item_id or item.get('mediaType') != ('book' if kind == 'audiobook' else 'podcast'):
            raise BridgeError('Audiobookshelf returned a different item type.')
        media = item.get('media') or {}
        if not isinstance(media, dict):
            raise BridgeError('Invalid Audiobookshelf media metadata.')
        files = media.get('audioFiles') if kind == 'audiobook' else media.get('episodes')
        if files is None:
            files = []
        if not isinstance(files, list) or len(files) > 1000:
            raise BridgeError('Invalid Audiobookshelf audio entries.')
        raw_entries = []
        for n, entry in enumerate(files, 1):
            if not isinstance(entry, dict):
                continue
            if kind == 'audiobook':
                details = entry.get('metadata') or {}
                if not isinstance(details, dict):
                    continue
                raw_entries.append((details.get('filename') or 'Part ' + str(n), entry.get('ino')))
            else:
                audio = entry.get('audioFile') or {}
                if not isinstance(audio, dict):
                    continue
                raw_entries.append((entry.get('title') or 'Episode ' + str(n), audio.get('ino')))
        if len(raw_entries) > 1000:
            raise BridgeError('Too many audio entries.')
        entries = []
        file_entries = []
        for title, inode in raw_entries:
            inode = str(inode)
            if not INO.fullmatch(inode):
                file_entries.append(None)
                continue
            capability = secrets.token_urlsafe(32)
            with self.lock:
                self.capabilities[capability] = (item_id, inode, self.clock() + TTL)
            entry = {'title': (title if isinstance(title, str) else 'Audio')[:160],
                     'url': 'http://127.0.0.1:' + str(self.http.server_port) + '/audio/' + capability}
            entries.append(entry)
            file_entries.append(entry)
        if kind == 'audiobook' and len(file_entries) == len(files) and all(file_entries):
            chapters = chapter_starts(media, files)
            if chapters:
                chapter_entries = []
                for title, index, offset, duration, number in chapters:
                    # Kodi keys music playlist entries by URL. Distinct capabilities
                    # prevent later chapters of the same file replacing this offset.
                    capability = secrets.token_urlsafe(32)
                    with self.lock:
                        self.capabilities[capability] = (item_id, str(files[index]['ino']), self.clock() + TTL)
                    chapter_entries.append({'title': title,
                                            'url': 'http://127.0.0.1:' + str(self.http.server_port) + '/audio/' + capability,
                                            'start_offset': offset, 'duration': duration, 'number': number})
                return chapter_entries
        for number, entry in enumerate(entries, 1):
            entry['number'] = number
        return entries

    def lookup(self, path):
        match = CAP.fullmatch(path)
        if not match:
            return None
        with self.lock:
            entry = self.capabilities.get(match.group(1))
            if entry and entry[2] < self.clock():
                del self.capabilities[match.group(1)]
                return None
            return entry

    def start(self, socket_path):
        bridge = self

        class ThreadedHTTP(socketserver.ThreadingMixIn, http.server.HTTPServer):
            daemon_threads = True
            allow_reuse_address = False

        class AudioHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return  # Capabilities and upstream paths must not enter Kodi logs.

            def do_HEAD(self):
                self.serve_audio('HEAD')

            def do_GET(self):
                self.serve_audio('GET')

            def serve_audio(self, method):
                if self.headers.get('Host') != '127.0.0.1:' + str(bridge.http.server_port):
                    self.send_error(403)
                    return
                entry = bridge.lookup(self.path)
                byte_range = self.headers.get('Range')
                if not entry or (byte_range and not RANGE.fullmatch(byte_range)):
                    self.send_error(404)
                    return
                item_id, inode, _ = entry
                try:
                    upstream = bridge.upstream('/api/items/' + item_id + '/file/' + inode + '/download',
                                               byte_range, method)
                except urllib.error.HTTPError as exc:
                    self.send_error(exc.code if exc.code in (401, 404, 416) else 502)
                    return
                except (urllib.error.URLError, OSError, BridgeError):
                    self.send_error(502)
                    return
                with upstream:
                    if upstream.status not in (200, 206, 416):
                        self.send_error(502)
                        return
                    self.send_response(upstream.status)
                    for header in ('Content-Type', 'Content-Length', 'Content-Range', 'Accept-Ranges'):
                        value = upstream.headers.get(header)
                        if value:
                            self.send_header(header, value)
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('X-Content-Type-Options', 'nosniff')
                    self.end_headers()
                    if method == 'GET':
                        try:
                            while True:
                                chunk = upstream.read(64 * 1024)
                                if not chunk:
                                    break
                                self.wfile.write(chunk)
                        except (BrokenPipeError, ConnectionResetError):
                            pass

        class ThreadedUnix(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
            daemon_threads = True

        class ControlHandler(socketserver.StreamRequestHandler):
            def handle(self):
                self.request.settimeout(10)
                try:
                    payload = self.rfile.readline(MAX_CONTROL + 1)
                    if len(payload) > MAX_CONTROL or not payload.endswith(b'\n'):
                        raise BridgeError('Invalid control request.')
                    request = json.loads(payload)
                    result = bridge.describe(request.get('kind'), request.get('item_id'))
                    answer = {'entries': result}
                except (BridgeError, ValueError, TypeError, KeyError):
                    answer = {'error': 'Audio bridge could not resolve this title.'}
                self.wfile.write((json.dumps(answer) + '\n').encode('utf-8'))

        self.http = ThreadedHTTP(('127.0.0.1', 0), AudioHandler)
        socket_path = str(socket_path)
        if os.path.lexists(socket_path):
            info = os.lstat(socket_path)
            if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
                raise BridgeError('Unsafe existing control socket.')
            os.unlink(socket_path)
        old_umask = os.umask(0o077)
        try:
            self.control = ThreadedUnix(socket_path, ControlHandler)
        finally:
            os.umask(old_umask)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.http_started = True
        threading.Thread(target=self.control.serve_forever, daemon=True).start()
        self.control_started = True

    def stop(self):
        if self.control:
            path = self.control.server_address
            if self.control_started:
                self.control.shutdown()
            self.control.server_close()
            os.unlink(path)
        if self.http:
            if self.http_started:
                self.http.shutdown()
            self.http.server_close()


def control_request(socket_path, kind, item_id):
    if not ID.fullmatch(item_id) or kind not in ('audiobook', 'podcast'):
        raise BridgeError('Invalid catalogue request.')
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(15)
        client.connect(str(socket_path))
        client.sendall((json.dumps({'kind': kind, 'item_id': item_id}) + '\n').encode('utf-8'))
        with client.makefile('rb') as response:
            raw = response.readline(256 * 1024 + 1)
    if len(raw) > 256 * 1024:
        raise BridgeError('Audio bridge response too large.')
    answer = json.loads(raw)
    if 'error' in answer:
        raise BridgeError(answer['error'])
    return answer['entries']
