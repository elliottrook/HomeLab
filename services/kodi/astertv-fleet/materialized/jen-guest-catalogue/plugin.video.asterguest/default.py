#!/usr/bin/env python3
"""Kodi routes for the isolated Guest film and television catalogue."""

from __future__ import annotations

import sys
import urllib.parse

import xbmcgui
import xbmcplugin

from client import GuestCatalogueError, item, items, libraries


HANDLE = int(sys.argv[1])
BASE = sys.argv[0]
PROXY = "http://127.0.0.1:57321"


def params():
    return dict(urllib.parse.parse_qsl(sys.argv[2].lstrip("?"), keep_blank_values=False))


def url(action, **values):
    return BASE + "?" + urllib.parse.urlencode({"action": action, **values})


def list_item(row, *, folder=False, playable=False):
    info = {"title": row["Name"], "plot": row.get("Overview", "")}
    if row.get("ProductionYear"):
        info["year"] = row["ProductionYear"]
    entry = xbmcgui.ListItem(label=row["Name"])
    entry.setInfo("video", info)
    if row.get("Id"):
        entry.setArt({"thumb": PROXY + "/art/" + row["Id"],
                      "poster": PROXY + "/art/" + row["Id"]})
    if playable:
        entry.setProperty("IsPlayable", "true")
    return entry


def add(path, row, *, folder=False, playable=False):
    xbmcplugin.addDirectoryItem(HANDLE, path, list_item(
        row, folder=folder, playable=playable), isFolder=folder)


def root():
    for row in libraries():
        kind = "Movie" if row["CollectionType"] == "movies" else "Series"
        add(url("browse", parent=row["Id"], kind=kind), row, folder=True)


def browse(arguments):
    kind = arguments["kind"]
    for row in items(arguments["parent"], kind):
        add(url("details", item=row["Id"]), row, folder=True)


def details(arguments):
    row = item(arguments["item"])
    if row["Type"] == "Movie":
        add(url("play", item=row["Id"]), {**row, "Name": "Play " + row["Name"]},
            playable=True)
    elif row["Type"] == "Series":
        for child in items(row["Id"], "Season"):
            add(url("details", item=child["Id"]), child, folder=True)
    elif row["Type"] == "Season":
        for child in items(row["Id"], "Episode"):
            add(url("details", item=child["Id"]), child, folder=True)
    elif row["Type"] == "Episode":
        add(url("play", item=row["Id"]), {**row, "Name": "Play " + row["Name"]},
            playable=True)


def play(arguments):
    row = item(arguments["item"])
    if row["Type"] not in ("Movie", "Episode"):
        raise GuestCatalogueError("playback-type-denied")
    resolved = list_item(row, playable=True)
    resolved.setPath(PROXY + "/stream/" + row["Id"] + "/master.m3u8")
    resolved.setMimeType("application/vnd.apple.mpegurl")
    resolved.setContentLookup(False)
    resolved.setProperty("inputstream", "inputstream.adaptive")
    resolved.setProperty("inputstream.adaptive.manifest_type", "hls")
    xbmcplugin.setResolvedUrl(HANDLE, True, resolved)


try:
    arguments = params()
    action = arguments.get("action", "root")
    {"root": lambda _value: root(), "browse": browse,
     "details": details, "play": play}[action](arguments)
    if action != "play":
        xbmcplugin.setContent(HANDLE, "movies")
        xbmcplugin.endOfDirectory(HANDLE, succeeded=True, cacheToDisc=False)
except (GuestCatalogueError, OSError, ValueError, KeyError):
    xbmcgui.Dialog().notification("Aster Guest", "Guest catalogue unavailable", time=3000)
    xbmcplugin.endOfDirectory(HANDLE, succeeded=False, cacheToDisc=False)
