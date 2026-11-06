"""Render AsterTV Kodi view nodes without touching the client or media.

The caller must first reconcile Kodi series IDs against ARR identities and
classify each season from the persisted lifecycle ledger. Numeric Kodi DB
routes distinguish shows that share a display title.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass(frozen=True)
class SeasonView:
    number: int
    archive: bool


@dataclass(frozen=True)
class SeriesView:
    kodi_id: int
    display_title: str
    seasons: tuple[SeasonView, ...]


def _xml(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _folder_index(label: str, order: int = 1) -> bytes:
    node = ET.Element("node", {"order": str(order)})
    ET.SubElement(node, "label").text = label
    return _xml(node)


def _season_node(kodi_id: int, season: SeasonView, order: int) -> bytes:
    node = ET.Element("node", {"order": str(order), "type": "folder"})
    number = season.number
    ET.SubElement(node, "label").text = "Specials" if number == 0 else f"Season {number:02d}"
    ET.SubElement(node, "path").text = f"videodb://tvshows/titles/{kodi_id}/{number}/"
    return _xml(node)


def render_tv_nodes(series: tuple[SeriesView, ...]) -> dict[str, bytes]:
    """Return a relative-path-to-XML tree for Current and Archive TV views."""
    ids: set[int] = set()
    for show in series:
        if show.kodi_id <= 0 or not show.display_title.strip():
            raise ValueError("series requires a positive Kodi ID and title")
        if show.kodi_id in ids:
            raise ValueError("duplicate Kodi series ID")
        ids.add(show.kodi_id)
        season_numbers = [season.number for season in show.seasons]
        if any(number < 0 for number in season_numbers) or len(set(season_numbers)) != len(season_numbers):
            raise ValueError("season numbers must be non-negative and unique per series")

    output = {
        "current-tv/index.xml": _folder_index("Current TV"),
        "archive-tv/index.xml": _folder_index("Archive TV"),
    }
    for archive, root in ((False, "current-tv"), (True, "archive-tv")):
        visible = [show for show in series if any(season.archive == archive for season in show.seasons)]
        for order, show in enumerate(sorted(visible, key=lambda item: item.display_title.casefold()), 1):
            parent = f"{root}/show-{show.kodi_id}"
            output[f"{parent}/index.xml"] = _folder_index(show.display_title, order)
            seasons = sorted((season for season in show.seasons if season.archive == archive), key=lambda item: item.number)
            for season_order, season in enumerate(seasons, 1):
                output[f"{parent}/season-{season.number:02d}.xml"] = _season_node(show.kodi_id, season, season_order)
    return output
