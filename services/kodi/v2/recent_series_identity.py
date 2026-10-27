"""Exact HP successor for native Recently Added series identity."""

from __future__ import annotations

import ast
import hashlib


PREDECESSOR = "50c5ecb4d676bdff544d47cfadd8f984a5f79b7d57a2af42682dbc3c7012dfb2"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def render(raw):
    if sha(raw) != PREDECESSOR:
        raise ValueError("recent-series-identity-predecessor")
    text = raw.decode()
    old = "    if row['kind'] == 'tvshow':\n        url = f\"videodb://tvshows/titles/{row['id']}/\""
    new = ("    if row['kind'] == 'tvshow':\n"
           "        if type(row.get('id')) is int:\n"
           "            item.getVideoInfoTag().setDbId(row['id'])\n"
           "        url = f\"videodb://tvshows/titles/{row['id']}/\"")
    if text.count(old) != 1:
        raise ValueError("recent-series-identity-anchor")
    text = text.replace(old, new)
    ast.parse(text)
    return text.encode()
