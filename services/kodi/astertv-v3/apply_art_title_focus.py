#!/usr/bin/env python3
"""Apply the shared v3 focus surface only to artwork-with-title tiles."""

from __future__ import annotations

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET


ART_MARKERS = (
    "ListItem.Art(",
    "AsterCardArt",
    "AsterPosterArt",
)
RING_TEXTURES = (
    "ui-compact-card-ring.png",
    "ui-album-ring.png",
    "ui-poster-ring.png",
)
BOOK_TILE_INCLUDES = {"AsterBooksTile", "AsterBooksSmallTile"}
EXPECTED_LAYOUTS = {
    "Home.xml": 2,
    "Includes.xml": 1,
    "IncludesBooks.xml": 2,
    "IncludesMusic.xml": 1,
    "MyVideoNav.xml": 4,
    "custom_1130_movie.xml": 2,
    "custom_1132_requests.xml": 1,
    "custom_1133_acquisition.xml": 1,
}


def number(node: ET.Element, name: str) -> int | None:
    value = node.findtext(name)
    try:
        return int(value) if value is not None else 0
    except ValueError:
        return None


def texture_text(control: ET.Element) -> str:
    texture = control.find("texture")
    return "" if texture is None or texture.text is None else texture.text


def is_art(control: ET.Element) -> bool:
    return control.get("type") == "image" and any(
        marker in texture_text(control) for marker in ART_MARKERS
    )


def has_title_below(layout: ET.Element, art: ET.Element) -> bool:
    art_top = number(art, "top")
    art_height = number(art, "height")
    if art_top is None or art_height is None:
        return False
    art_bottom = art_top + art_height
    for label in title_controls(layout):
        label_top = number(label, "top")
        if label_top is not None and label_top >= art_bottom - 12:
            return True
    return False


def is_book_template(layout: ET.Element) -> bool:
    return any(
        include.text in BOOK_TILE_INCLUDES
        for include in layout.findall("include")
        if include.text
    )


def title_controls(layout: ET.Element) -> list[ET.Element]:
    return [
        control
        for control in layout.findall("control")
        if control.get("type") in {"label", "textbox"}
    ]


def has_shared_surface(layout: ET.Element) -> bool:
    return any(
        control.get("type") == "image"
        and control.find("texture") is not None
        and control.find("texture").get("colordiffuse") == "asterSageGlass"
        for control in layout.findall("control")
    )


def remove_legacy_focus_art(layout: ET.Element) -> None:
    for control in list(layout.findall("control[@type='image']")):
        texture = texture_text(control)
        diffuse = control.findtext("colordiffuse")
        if any(texture.endswith(name) for name in RING_TEXTURES):
            layout.remove(control)
        elif texture.endswith("ui-panel.png") and diffuse == "asterGreen":
            layout.remove(control)


def add_shared_surface(layout: ET.Element) -> None:
    width = int(layout.get("width", "0"))
    height = int(layout.get("height", "0"))
    if width < 80 or height < 80:
        raise ValueError(f"unsafe tile dimensions {width}x{height}")
    control = ET.Element("control", {"type": "image"})
    for name, value in (
        ("left", "0"),
        ("top", "0"),
        ("width", str(width - 4)),
        ("height", str(height - 4)),
    ):
        ET.SubElement(control, name).text = value
    texture = ET.SubElement(
        control,
        "texture",
        {"border": "24", "colordiffuse": "asterSageGlass"},
    )
    texture.text = "special://skin/media/ui-panel.png"
    layout.insert(0, control)


def normalize_title_contrast(layout: ET.Element, art: ET.Element | None) -> None:
    art_bottom = None
    if art is not None:
        art_top = number(art, "top")
        art_height = number(art, "height")
        if art_top is not None and art_height is not None:
            art_bottom = art_top + art_height
    for label in title_controls(layout):
        label_top = number(label, "top")
        if art_bottom is None or (
            label_top is not None and label_top >= art_bottom - 12
        ):
            textcolor = label.find("textcolor")
            if textcolor is not None:
                textcolor.text = "asterInk"


def transform_file(path: Path) -> int:
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    tree = ET.parse(path, parser=parser)
    changed = 0
    for layout in tree.getroot().iter("focusedlayout"):
        art = next((node for node in layout.findall("control") if is_art(node)), None)
        qualifies = (art is not None and has_title_below(layout, art)) or is_book_template(layout)
        if not qualifies or has_shared_surface(layout):
            continue
        remove_legacy_focus_art(layout)
        add_shared_surface(layout)
        normalize_title_contrast(layout, art)
        changed += 1
    if changed:
        tree.write(path, encoding="utf-8", xml_declaration=True)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skin", type=Path)
    args = parser.parse_args()
    skin = args.skin.resolve()
    views = skin / "1080i"
    if not views.is_dir() or skin.name != "skin.asterhome.v3pilot":
        raise SystemExit(f"refusing unexpected skin path: {skin}")
    changed = 0
    touched: dict[str, int] = {}
    for path in sorted(views.glob("*.xml")):
        file_count = transform_file(path)
        if file_count:
            touched[path.name] = file_count
            changed += file_count
    if touched != EXPECTED_LAYOUTS:
        raise SystemExit(
            "art/title layout inventory changed: "
            f"expected {EXPECTED_LAYOUTS}, found {touched}"
        )
    print(f"Applied shared art/title focus to {changed} focused layouts")
    print("Touched " + ", ".join(f"{name}:{count}" for name, count in touched.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
