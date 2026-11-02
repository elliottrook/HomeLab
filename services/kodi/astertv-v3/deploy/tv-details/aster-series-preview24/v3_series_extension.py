"""AsterTV v3 presentation extension for the proven v2 series engine.

The module deliberately leaves playback ownership, queue handling and recovery
with ``default.py``.  It only supplies the accepted v3 season/cast/related
rails and the bounded trailer/actor routes.
"""
from __future__ import annotations

import json
from urllib.parse import quote

import xbmc
import xbmcgui


def _rpc(method, params=None):
    answer = json.loads(xbmc.executeJSONRPC(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}
    })))
    if "error" in answer:
        return {}
    return answer.get("result", {})


def _art(row, *names):
    art = row.get("art") or {}
    for name in names:
        value = art.get(name)
        if value:
            return value
    return row.get("thumbnail") or ""


def _list_item(label, thumb="", **properties):
    item = xbmcgui.ListItem(label=label)
    if thumb:
        item.setArt({"thumb": thumb})
    for key, value in properties.items():
        item.setProperty(key, str(value))
    return item


def _details(show_id):
    return (_rpc("VideoLibrary.GetTVShowDetails", {
        "tvshowid": int(show_id),
        "properties": ["title", "genre", "year", "art", "cast", "trailer"]
    }).get("tvshowdetails") or {})


def _populate_v3(self):
    # Specials (season 0) are not part of the normal season chooser.  Keep an
    # explicit absolute-index map because SeriesSelection still owns the full
    # page model and may include specials internally.
    visible_seasons = [
        index for index, group in enumerate(self.snapshot.page.seasons)
        if group.number not in (None, 0)
    ]
    self._v3_season_indices = visible_seasons
    seasons = []
    current = self.selection.season
    for index in visible_seasons:
        group = self.snapshot.page.seasons[index]
        seasons.append(_list_item(str(group.number), "", Index=index,
                                  Current="true" if index == current else "false"))
    control = self.getControl(612)
    control.reset()
    control.addItems(seasons)
    control.setHeight(min(len(seasons), 8) * 88)
    if seasons:
        selected = visible_seasons.index(current) if current in visible_seasons else 0
        control.selectItem(selected)

    details = _details(self.snapshot.page.show_id)
    self._v3_trailer = details.get("trailer") or ""
    cast = []
    for person in (details.get("cast") or [])[:24]:
        name = person.get("name") or ""
        if name:
            cast.append(_list_item(name, person.get("thumbnail") or "", Name=name))
    cast_control = self.getControl(610)
    cast_control.reset()
    cast_control.addItems(cast)

    wanted = {str(x).casefold() for x in (details.get("genre") or self.snapshot.genres)}
    catalogue = _rpc("VideoLibrary.GetTVShows", {
        "properties": ["title", "genre", "year", "art"],
        "limits": {"start": 0, "end": 500}
    }).get("tvshows") or []
    ranked = []
    for row in catalogue:
        if int(row.get("tvshowid") or 0) == int(self.snapshot.page.show_id):
            continue
        genres = {str(x).casefold() for x in (row.get("genre") or [])}
        overlap = len(wanted & genres)
        if overlap:
            ranked.append((overlap, int(row.get("year") or 0), row))
    ranked.sort(key=lambda value: (-value[0], -value[1], value[2].get("title", "")))
    related = []
    self._v3_related = []
    for _, _, row in ranked[:16]:
        identity = int(row.get("tvshowid") or 0)
        related.append(_list_item(row.get("title") or "", _art(row, "fanart", "thumb", "poster"),
                                  TvShowId=identity))
        self._v3_related.append(identity)
    related_control = self.getControl(611)
    related_control.reset()
    related_control.addItems(related)


def install(series_class):
    original_init = series_class.onInit
    original_populate = series_class.populate
    original_click = series_class.onClick

    def on_init(self):
        original_init(self)
        try:
            _populate_v3(self)
        except Exception as error:
            xbmc.log("AsterTV v3 series enrichment: " + repr(error), xbmc.LOGERROR)

    def populate(self):
        original_populate(self)
        if getattr(self, "ready", False):
            try:
                _populate_v3(self)
            except Exception as error:
                xbmc.log("AsterTV v3 series refresh: " + repr(error), xbmc.LOGERROR)

    def on_click(self, identity):
        if identity == 202:
            self.close()
            return
        if identity in (200, 203):
            original_click(self, 200)
            return
        if identity == 204:
            trailer = getattr(self, "_v3_trailer", "")
            if trailer.startswith("plugin://plugin.video.youtube/"):
                xbmc.executebuiltin("PlayMedia(" + trailer + ")")
            else:
                xbmcgui.Dialog().notification("AsterTV", "No verified trailer is available")
            return
        if identity == 612:
            position = self.getControl(612).getSelectedPosition()
            visible_seasons = getattr(self, "_v3_season_indices", [])
            if not 0 <= position < len(visible_seasons):
                return
            self.updating = True
            try:
                absolute = visible_seasons[position]
                number = self.snapshot.page.seasons[absolute].number
                self.load_catalogue_season(number)
                position = next(i for i, row in enumerate(self.snapshot.page.seasons)
                                if row.number == number)
                self.selection.change_season(position)
                original_populate(self)
                _populate_v3(self)
                self.setFocusId(300)
            finally:
                self.updating = False
            self.publish()
            return
        if identity == 610:
            item = self.getControl(610).getSelectedItem()
            name = item.getProperty("Name") if item else ""
            if name:
                route = "plugin://plugin.video.astersearch/?actor=" + quote(name)
                command = 'ActivateWindow(Videos,"' + route + '",return)'
                xbmc.executebuiltin("AlarmClock(AsterActor," + command + ",00:00:01,silent)")
                self.close()
            return
        if identity == 611:
            item = self.getControl(611).getSelectedItem()
            target = item.getProperty("TvShowId") if item else ""
            if target.isdecimal():
                command = "RunScript(script.asterruntime,aster-series-preview24,default," + target + ",play)"
                xbmc.executebuiltin("AlarmClock(AsterRelated," + command + ",00:00:02,silent)")
                self.close()
            return
        original_click(self, identity)

    def consume_command(self):
        command = self.getProperty("Series.Command")
        if not command:
            return
        self.clearProperty("Series.Command")
        if command != "select":
            return
        try:
            identity = self.getFocusId()
        except RuntimeError:
            return
        if identity in (200, 202, 203, 204, 300, 610, 611, 612):
            self.onClick(identity)

    class V3SeriesPreview(series_class):
        def onInit(self):
            return on_init(self)

        def populate(self):
            return populate(self)

        def onClick(self, identity):
            return on_click(self, identity)

        def consume_command(self):
            return consume_command(self)

    return V3SeriesPreview
