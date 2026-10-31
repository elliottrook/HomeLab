"""Content-free lab diagnostics for the r13 TV/Seerr acceptance repair."""
import json
import sys
import time

import xbmc
import xbmcgui


def rpc(method, params=None):
    answer = json.loads(xbmc.executeJSONRPC(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}
    })))
    return answer.get("result", {})


def log(name, **values):
    xbmc.log("AsterR13Test: " + name + " " + json.dumps(values, sort_keys=True), xbmc.LOGINFO)


def wait_for(check, seconds=12):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = check()
        if value:
            return value
        xbmc.sleep(100)
    return None


def launch_series():
    shows = rpc("VideoLibrary.GetTVShows", {"properties": ["episode"], "limits": {"start": 0, "end": 50}}).get("tvshows", [])
    chosen = None
    for row in shows:
        seasons = rpc("VideoLibrary.GetSeasons", {
            "tvshowid": row["tvshowid"], "properties": ["season"]}).get("seasons", [])
        populated = [season for season in seasons
                     if rpc("VideoLibrary.GetEpisodes", {
                         "tvshowid": row["tvshowid"], "season": season["season"],
                         "limits": {"start": 0, "end": 1}}).get("episodes")]
        if len(populated) > 1:
            chosen = row["tvshowid"]
            break
    if chosen is None:
        raise RuntimeError("no multi-season test item")
    xbmc.executebuiltin("RunScript(script.asterruntime,aster-series-preview24,default,%d,play)" % chosen)
    log("series-launch", multi_season=True)


def series_state(stage):
    home = xbmcgui.Window(10000)
    identity = wait_for(lambda: home.getProperty("AsterSeries.PreviewWindow"), 15)
    if not identity:
        log(stage, ready=False)
        return
    identity = int(identity)
    window = xbmcgui.Window(identity)
    focus = window.getFocusId()
    log(stage, ready=True, current=xbmcgui.getCurrentWindowId(), identity=identity,
        focus=focus, episodes=window.getControl(300).size(),
        season_menu=window.getProperty("Series.SeasonMenu"),
        season_index=window.getProperty("Series.SeasonIndex"))


def open_series_seasons():
    home = xbmcgui.Window(10000)
    identity = wait_for(lambda: home.getProperty("AsterSeries.PreviewWindow"), 10)
    if not identity:
        return log("series-menu", ready=False)
    window = xbmcgui.Window(int(identity))
    window.setFocusId(201)
    window.setProperty("Series.Command", "select")
    opened = wait_for(lambda: (not window.getProperty("Series.Command") and
                               window.getProperty("Series.SeasonMenu") == "true"), 5)
    xbmc.sleep(300)
    log("series-menu", ready=bool(opened), focus=window.getFocusId(),
        row0=bool(window.getProperty("Series.SeasonRow0")),
        row1=bool(window.getProperty("Series.SeasonRow1")))


def choose_series_season():
    home = xbmcgui.Window(10000)
    identity = wait_for(lambda: home.getProperty("AsterSeries.PreviewWindow"), 10)
    if not identity:
        return log("series-season", ready=False)
    window = xbmcgui.Window(int(identity))
    before = window.getProperty("Series.SeasonIndex")
    menu_before = window.getProperty("Series.SeasonMenu")
    target = 312 if window.getProperty("Series.SeasonRow1") else 311
    window.setFocusId(target)
    window.setProperty("Series.Command", "select")
    changed = wait_for(lambda: (not window.getProperty("Series.Command") and
                                window.getProperty("Series.SeasonMenu") == "false"), 8)
    xbmc.sleep(300)
    log("series-season", ready=bool(changed), before=before,
        after=window.getProperty("Series.SeasonIndex"), focus=window.getFocusId(),
        episodes=window.getControl(300).size(), menu_before=menu_before)


def seerr_seasons():
    home = xbmcgui.Window(10000)
    if not wait_for(lambda: xbmc.getCondVisibility("Window.IsActive(11132)"), 12):
        return log("seerr-season", ready=False, reason="window")
    window = xbmcgui.Window(11132)
    results = window.getControl(30)
    kinds = sorted({results.getListItem(index).getProperty("Kind")
                    for index in range(results.size())})
    tv = next((index for index in range(results.size())
               if results.getListItem(index).getProperty("Kind").lower() in ("tv", "television")), None)
    if tv is None:
        return log("seerr-season", ready=False, reason="no-tv-candidate", kinds=kinds,
                   results=results.size())
    results.selectItem(tv)
    if not wait_for(lambda: home.getProperty("AsterSeerr.SeasonsVisible") == "true", 10):
        return log("seerr-season", ready=False, reason="no-seasons")
    seasons = window.getControl(40)
    seasons.selectItem(0)
    before = seasons.getListItem(0).getLabel()
    window.setFocusId(40)
    home.setProperty("AsterSeerr.Command", "season")
    changed = wait_for(lambda: seasons.getListItem(0).getLabel() != before, 5)
    log("seerr-season", ready=bool(changed), focus=window.getFocusId(),
        seasons=seasons.size(), selection_changed=bool(changed))


MODES = {
    "launch-series": launch_series,
    "series-state": lambda: series_state("series-state"),
    "series-menu": open_series_seasons,
    "series-season": choose_series_season,
    "seerr-season": seerr_seasons,
}
MODES[sys.argv[1]]()
