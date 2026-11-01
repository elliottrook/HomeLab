"""Read-only actor results from Kodi's Jellyfin-synchronised video library."""

import json
import sys
import traceback
from urllib.parse import parse_qs

import xbmc
import xbmcgui
import xbmcplugin

from actor_search import clean_actor


BASE_PROPERTIES = [
    "title", "plot", "year", "genre", "rating", "mpaa", "art", "file",
    "runtime", "playcount",
]
MOVIE_PROPERTIES = BASE_PROPERTIES + ["resume"]
TVSHOW_PROPERTIES = BASE_PROPERTIES


def rpc(method, actor, properties):
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": {
            "filter": {"field": "actor", "operator": "is", "value": actor},
            "properties": properties,
            "sort": {"method": "title", "order": "ascending"},
            "limits": {"start": 0, "end": 500},
        },
    }
    response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if "error" in response:
        raise ValueError(response["error"].get("message", "Kodi library query failed"))
    return response.get("result", {})


def add_result(handle, row, kind):
    identity_key = "movieid" if kind == "movie" else "tvshowid"
    identity = row.get(identity_key)
    if type(identity) is not int:
        return False
    title = row.get("label") or row.get("title") or "Untitled"
    item = xbmcgui.ListItem(label=title)
    item.setInfo("video", {
        "title": title,
        "plot": row.get("plot", ""),
        "year": row.get("year", 0),
        "genre": row.get("genre", []),
        "rating": row.get("rating", 0),
        "mpaa": row.get("mpaa", ""),
        "duration": row.get("runtime", 0),
        "mediatype": kind,
    })
    art = row.get("art") if isinstance(row.get("art"), dict) else {}
    if art:
        item.setArt(art)
    item.getVideoInfoTag().setDbId(identity)
    if kind == "tvshow":
        url = "videodb://tvshows/titles/{}/".format(identity)
        xbmcplugin.addDirectoryItem(handle, url, item, isFolder=True)
    else:
        url = row.get("file", "")
        item.setProperty("IsPlayable", "true")
        xbmcplugin.addDirectoryItem(handle, url, item, isFolder=False)
    return True


def main():
    handle = int(sys.argv[1])
    query = parse_qs(sys.argv[2].lstrip("?"))
    try:
        actor = clean_actor(query.get("actor", [""])[0])
        movie_rows = rpc("VideoLibrary.GetMovies", actor, MOVIE_PROPERTIES).get("movies", [])
        show_rows = rpc("VideoLibrary.GetTVShows", actor, TVSHOW_PROPERTIES).get("tvshows", [])
        if not isinstance(movie_rows, list) or not isinstance(show_rows, list):
            raise ValueError("invalid library result")
        xbmcplugin.setPluginCategory(
            handle,
            "{} — Movie and TV credits available on AsterTV".format(actor),
        )
        xbmcplugin.setContent(handle, "videos")
        count = 0
        for row in movie_rows:
            count += int(isinstance(row, dict) and add_result(handle, row, "movie"))
        for row in show_rows:
            count += int(isinstance(row, dict) and add_result(handle, row, "tvshow"))
        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
        if not count:
            xbmcgui.Dialog().notification("Aster Media", "No library titles found for {}".format(actor))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        xbmc.log("Aster actor search: {}\n{}".format(error, traceback.format_exc()), xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Aster Media", "Actor search could not be completed")
        xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)


if __name__ == "__main__":
    main()
