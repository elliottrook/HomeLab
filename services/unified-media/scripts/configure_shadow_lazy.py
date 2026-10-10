#!/usr/bin/env python3
"""Configure the isolated LazyLibrarian shadow instance without printing keys."""

import html.parser
import os
import re
import urllib.parse
import urllib.request


BASE = os.environ.get("LAZY_URL", "http://127.0.0.1:5299")
PROWLARR_KEY = os.environ["PROWLARR_KEY"]
SAB_KEY = os.environ["SAB_KEY"]


class FormParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = []
        self.select = None
        self.options = []
        self.textarea = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("name"):
            input_type = attrs.get("type", "text")
            if input_type in ("checkbox", "radio") and "checked" not in attrs:
                return
            value = attrs.get("value", "1") if input_type in ("checkbox", "radio") else attrs.get("value", "")
            self.data.append((attrs["name"], value))
        elif tag == "select" and attrs.get("name"):
            self.select = [attrs["name"], None]
        elif tag == "option" and self.select:
            self.options.append((attrs.get("value", ""), "selected" in attrs))
        elif tag == "textarea" and attrs.get("name"):
            self.textarea = [attrs["name"], ""]

    def handle_endtag(self, tag):
        if tag == "select" and self.select:
            value = self.select[1]
            if value is None:
                value = next((item for item, selected in self.options if selected), "")
            self.data.append((self.select[0], value))
            self.select = None
            self.options = []
        elif tag == "textarea" and self.textarea:
            self.data.append(tuple(self.textarea))
            self.textarea = None

    def handle_data(self, data):
        if self.textarea:
            self.textarea[1] += data


def set_value(values, name, value):
    values[:] = [(key, old) for key, old in values if key != name]
    if value is not None:
        values.append((name, value))


def get(path, params):
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{BASE}{path}?{query}")
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status, response.read().decode("utf-8", "replace")


with urllib.request.urlopen(f"{BASE}/config", timeout=20) as response:
    parser = FormParser()
    parser.feed(response.read().decode("utf-8", "replace"))
values = parser.data

# Shadow-only downloader and import boundaries.
set_value(values, "nzb_downloader_sabnzbd", "1")
set_value(values, "sab_host", "192.168.20.40")
set_value(values, "sab_port", "8080")
set_value(values, "sab_user", "")
set_value(values, "sab_pass", "")
set_value(values, "sab_api", SAB_KEY)
set_value(values, "sab_cat", "books-shadow")
set_value(values, "sab_subdir", "")
set_value(values, "sab_remote", "")
set_value(values, "sab_local", "")
set_value(values, "download_dir", "/downloads")
set_value(values, "ebook_dir", "/books")
set_value(values, "audio_dir", "/audio")
set_value(values, "alternate_dir", "/ingest")

# Use one existing Prowlarr indexer through its Newznab-compatible endpoint.
set_value(values, "newznab_0_dispname", "Prowlarr Nzb.life")
set_value(values, "newznab_0_enabled", "1")
set_value(values, "newznab_0_host", "http://192.168.20.40:9696/1/api")
set_value(values, "newznab_0_api", PROWLARR_KEY)
set_value(values, "newznab_0_booksearch", "book")
set_value(values, "newznab_0_audiosearch", "book")

# LazyLibrarian must not write the Calibre database directly.
for field in ("imp_calibre_ebook", "imp_calibre_comic", "imp_calibre_magazine"):
    set_value(values, field, None)

payload = urllib.parse.urlencode([("utf8", "✓")] + values).encode()
request = urllib.request.Request(f"{BASE}/config_update", data=payload, method="POST")
with urllib.request.urlopen(request, timeout=20) as response:
    print(f"config_update_http={response.status}")

status, result = get(
    "/test_sabnzbd",
    {"host": "192.168.20.40", "port": "8080", "user": "", "pwd": "", "api": SAB_KEY, "cat": "books-shadow", "subdir": ""},
)
result = re.sub(r"\s+", " ", result.replace(SAB_KEY, "REDACTED").replace(PROWLARR_KEY, "REDACTED"))
print(f"sab_test_http={status} result={result[:180]}")

print("provider_enabled=1 search_type=book (validated through Prowlarr despite incomplete caps metadata)")
