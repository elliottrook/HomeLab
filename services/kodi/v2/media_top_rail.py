"""Formatting-preserving correction for the crowded Media top rail."""

import hashlib
import re
import xml.etree.ElementTree as ET

from seerr_home_launcher import _button, _group_bounds, _visible_label


ACCEPTED_HOME = "8b3867e46ec38e8e43b0fb8177a63ca3f4efbdcbd502f6121cc489a857d4d83b"

ROWS = (
    (135, 350, 170, "Search",
     "RunScript(script.asterruntime,aster-global-search-ui22,default)",
     136, 130, 121, ""),
    (130, 540, 150, "TV Shows",
     "ActivateWindow(Videos,special://skin/playlists/tv-shows.xsp,return)",
     135, 131, 120, "special://skin/media/07-tv.png"),
    (131, 700, 130, "Movies",
     "ActivateWindow(Videos,special://skin/playlists/movies.xsp,return)",
     130, 132, 120, "special://skin/media/08-film.png"),
    (132, 840, 165, "Archive TV",
     "ActivateWindow(Videos,special://skin/playlists/archive-tv.xsp,return)",
     131, 133, 120, "special://skin/media/09-archive-tv.png"),
    (133, 1015, 210, "Archive Movies",
     "ActivateWindow(Videos,special://skin/playlists/archive-film.xsp,return)",
     132, 134, 120, "special://skin/media/10-archive-film.png"),
    (134, 1235, 163, "Collections",
     "ActivateWindow(Videos,videodb://movies/sets/,return)",
     133, 136, 120, "special://skin/media/19-movie-collections-128.png"),
    (136, 1408, 165, "YouTube",
     "ActivateWindow(Videos,&quot;plugin://plugin.video.youtube/&quot;,return)",
     134, 135, 121, "special://skin/media/33-aster-youtube-128.png"),
)


def require(value, code):
    if not value:
        raise ValueError(code)


def group():
    buttons = "\n".join(_button(*row[:8]) for row in ROWS)
    labels = _visible_label(*ROWS[0][:4], ROWS[0][8])
    labels += "".join(
        _visible_label(row[0], row[1], row[2], row[3], row[8]).replace(
            "<font>font20</font>", "<font>font18</font>")
        for row in ROWS[1:])
    # Destination labels use the same family but one optical step smaller.  At
    # sofa distance this reads as one rail and prevents ellipses without moving
    # the clock or reducing the Search affordance.
    return f'''<control type="group" id="23">
            <control type="image"><left>532</left><top>23</top><width>1050</width><height>62</height><texture border="18" colordiffuse="52000000">special://skin/media/ui-panel.png</texture></control>
            <control type="image"><left>348</left><top>29</top><width>174</width><height>50</height><texture border="18" colordiffuse="75cbb991">special://skin/media/ui-compact-card-ring.png</texture></control>
            <animation effect="fade" start="100" end="0" time="0" condition="[Control.HasFocus(8999) | Control.HasFocus(9001) | Control.HasFocus(9002) | Control.HasFocus(9003) | Control.HasFocus(9004) | Control.HasFocus(9005) | Control.HasFocus(9007)] + !Skin.HasSetting(AsterReducedMotion)">Conditional</animation>
{buttons}
            {labels}
        </control>'''


def _contract(raw):
    root = ET.fromstring(raw)
    found = {}
    rail = root.find(".//control[@id='23']")
    require(rail is not None, "media-top-rail-missing")
    for row in ROWS:
        identity = str(row[0])
        control = rail.find(f"control[@id='{identity}']")
        require(control is not None, "media-top-rail-button")
        found[int(identity)] = {
            "label": control.findtext("label"),
            "onclick": control.findtext("onclick"),
            "down": control.findtext("ondown"),
        }
    return found


def transform(raw):
    require(isinstance(raw, bytes)
            and hashlib.sha256(raw).hexdigest() == ACCEPTED_HOME,
            "media-top-rail-predecessor")
    before = _contract(raw)
    text = raw.decode("utf-8")
    start, end = _group_bounds(text)
    result = (text[:start] + group() + text[end:]).encode("utf-8")
    after = _contract(result)
    require(before == after, "media-top-rail-semantic-drift")
    require(result.count(b"<label>Archive Movies</label>") == 2
            and b"<label>Requests</label>" not in result,
            "media-top-rail-label-regression")
    root = ET.fromstring(result)
    rail = root.find(".//control[@id='23']")
    buttons = [rail.find(f"control[@id='{row[0]}']") for row in ROWS]
    for first, second in zip(buttons[1:], buttons[2:]):
        require(int(first.findtext("left")) + int(first.findtext("width"))
                < int(second.findtext("left")), "media-top-rail-overlap")
    require(int(buttons[-1].findtext("left"))
            + int(buttons[-1].findtext("width")) <= 1738,
            "media-top-rail-clock-collision")
    return result
