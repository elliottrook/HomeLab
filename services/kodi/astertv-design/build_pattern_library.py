#!/usr/bin/env python3
"""Build the deterministic AsterTV asset index and synthetic pattern library."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GENERATED = HERE / "generated"
RUNTIME_ROOTS = [
    ROOT / "services/kodi/astertv-v3/overlay/skin.asterhome.v3pilot/media",
    ROOT / "services/kodi/astertv-v3/aster_client/addon/script.astertv.voice/resources/media",
    ROOT / "services/kodi/astertv-v3/deploy/tv-details/skin.asterhome/media",
    ROOT / "services/kodi/astertv-v2/reconciliation/payload/skin.asterhome/media",
    ROOT / "services/kodi/astertv-v3/brand_assets",
    ROOT / "services/aster-agent/static/remote",
]
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


def load(name: str):
    return json.loads((HERE / name).read_text())


def canonical(data) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(131072), b""):
            digest.update(block)
    return digest.hexdigest()


def runtime_assets() -> list[dict]:
    records: list[dict] = []
    for base in RUNTIME_ROOTS:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix.lower() in ASSET_SUFFIXES:
                records.append({
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                    "consumer": base.relative_to(ROOT).as_posix(),
                })
    return records


def raster_baseline_digest(records: list[dict], policy: dict) -> tuple[int, str]:
    placement_paths = {item["output_path"] for item in policy["placement_exports"]}
    exclusions = [item["path_fragment"] for item in policy["content_exclusions"]]
    rows = []
    for record in records:
        path = record["path"]
        if Path(path).suffix.lower() == ".svg" or path in placement_paths:
            continue
        if any(fragment in path for fragment in exclusions):
            continue
        rows.append({"path": path, "sha256": record["sha256"]})
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return len(rows), hashlib.sha256(payload).hexdigest()


def validate_asset_policy(catalogue: dict, policy: dict, records: list[dict]) -> list[str]:
    errors: list[str] = []
    if policy.get("master_format") != "svg":
        errors.append("asset-policy: master format must be svg")
    for asset in catalogue["semantic_assets"]:
        master = asset.get("master") or asset.get("repository_path")
        if not master or Path(master).suffix.lower() != ".svg":
            errors.append(f'{asset["id"]}: semantic master is not SVG')
        for export in asset.get("runtime_exports", []):
            if export.get("derived_from_svg_sha256") != asset.get("master_sha256"):
                errors.append(f'{asset["id"]}/{export.get("path")}: source SVG hash missing or mismatched')
            if not export.get("placement"):
                errors.append(f'{asset["id"]}/{export.get("path")}: placement missing')
            dimensions = export.get("dimensions")
            if not isinstance(dimensions, list) or len(dimensions) != 2 or not all(isinstance(value, int) and value > 0 for value in dimensions):
                errors.append(f'{asset["id"]}/{export.get("path")}: fixed dimensions missing')
            if not export.get("export_recipe"):
                errors.append(f'{asset["id"]}/{export.get("path")}: SVG export recipe missing')
            if export.get("runtime_resize_allowed") is not False:
                errors.append(f'{asset["id"]}/{export.get("path")}: runtime resizing must be forbidden')
        for export in asset.get("legacy_exports", []):
            if export.get("status") != "frozen-pre-policy" or export.get("runtime_resize_allowed") is not False:
                errors.append(f'{asset["id"]}/{export.get("path")}: legacy export must remain frozen')
    runtime_by_path = {item["path"]: item for item in records}
    for export in policy["placement_exports"]:
        source = export.get("source_svg_path", "")
        output = export.get("output_path", "")
        if Path(source).suffix.lower() != ".svg" or not re.fullmatch(r"[0-9a-f]{64}", export.get("source_svg_sha256", "")):
            errors.append(f"{output}: invalid source SVG provenance")
        if not export.get("placement") or export.get("runtime_resize_allowed") is not False:
            errors.append(f"{output}: placement export is not fixed to its consumer")
        dimensions = export.get("dimensions")
        if not isinstance(dimensions, list) or len(dimensions) != 2 or not all(isinstance(value, int) and value > 0 for value in dimensions):
            errors.append(f"{output}: fixed dimensions missing")
        if not export.get("export_recipe"):
            errors.append(f"{output}: SVG export recipe missing")
        record = runtime_by_path.get(output)
        if not record or record["sha256"] != export.get("output_sha256"):
            errors.append(f"{output}: placement export missing or hash mismatched")
    count, digest = raster_baseline_digest(records, policy)
    baseline = policy["legacy_raster_baseline"]
    if count != baseline["count"] or digest != baseline["sha256"]:
        errors.append("asset-policy: unregistered raster added or frozen legacy raster changed")
    return errors


def xml_controls(template: str) -> list[int]:
    if not template:
        return []
    path = ROOT / template
    if not path.exists():
        return []
    return sorted({int(value) for value in re.findall(r'<control[^>]+id="(\d+)"', path.read_text(errors="replace"))})


def validate_focus(graphs: dict) -> list[str]:
    errors: list[str] = []
    for graph in graphs["graphs"]:
        nodes = graph["nodes"]
        if graph["entry"] not in nodes:
            errors.append(f'{graph["page"]}: entry is not a node')
        for node, edges in nodes.items():
            for direction, target in edges.items():
                if direction not in {"left", "right", "up", "down"}:
                    errors.append(f'{graph["page"]}/{node}: invalid direction {direction}')
                if target not in nodes:
                    errors.append(f'{graph["page"]}/{node}: missing target {target}')
    return errors


def svg_escape(value: str) -> str:
    return html.escape(value, quote=True)


def svg_frame(title: str, body: str, tokens: dict) -> str:
    c = tokens["colors"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img" aria-label="{svg_escape(title)}">
<defs><linearGradient id="page" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#302820"/><stop offset=".42" stop-color="{c['charcoal']}"/><stop offset="1" stop-color="{c['warm_white']}"/></linearGradient><linearGradient id="art" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c['jade']}"/><stop offset="1" stop-color="{c['champagne_gold']}"/></linearGradient></defs>
<rect width="1920" height="1080" fill="url(#page)"/><text x="84" y="90" fill="{c['champagne_gold']}" font-family="sans-serif" font-size="32">AsterTV design authority</text><text x="84" y="140" fill="{c['warm_white']}" font-family="sans-serif" font-size="46">{svg_escape(title)}</text>{body}</svg>'''


def component_render(component: dict, tokens: dict) -> str:
    c = tokens["colors"]
    states = component["states"]
    variants = component["variants"]
    cells = []
    width = 1640 / max(1, min(4, len(states)))
    for index, state in enumerate(states):
        col = index % 4
        row = index // 4
        x = 110 + col * 410
        y = 230 + row * 220
        focused = state in {"focus", "pressed", "confirm"}
        fill = c["jade"] if focused else c["charcoal"]
        stroke = c["champagne_gold"]
        art = f'<rect x="{x+20}" y="{y+20}" width="118" height="118" rx="16" fill="url(#art)"/>' if component["id"] in {"artwork-tile", "content-rail", "identity"} else ""
        cells.append(f'<g><rect x="{x}" y="{y}" width="360" height="168" rx="28" fill="{fill}" fill-opacity=".9" stroke="{stroke}" stroke-width="{4 if focused else 2}"/>{art}<text x="{x+160 if art else x+28}" y="{y+76}" fill="{c["warm_white"]}" font-family="sans-serif" font-size="28">{svg_escape(state)}</text><text x="{x+160 if art else x+28}" y="{y+112}" fill="{c["soft_text"]}" font-family="sans-serif" font-size="19">{svg_escape(variants[index % len(variants)])}</text></g>')
    return svg_frame(component["id"].replace("-", " ").title(), "".join(cells), tokens)


def page_render(page: dict, tokens: dict) -> str:
    c = tokens["colors"]
    family = page["family"]
    tiles = []
    for i in range(5):
        x = 160 + i * 300
        tiles.append(f'<g><rect x="{x}" y="720" width="244" height="190" rx="18" fill="url(#art)"/><rect x="{x-4}" y="716" width="252" height="246" rx="20" fill="none" stroke="{c["jade"] if i == 0 else "transparent"}" stroke-width="4"/><text x="{x}" y="948" fill="{c["ink"]}" font-family="sans-serif" font-size="24">Synthetic item {i+1}</text></g>')
    pills = "".join(f'<rect x="{480+i*230}" y="62" width="200" height="56" rx="28" fill="{c["charcoal"]}" stroke="{c["champagne_gold"]}" stroke-width="2"/><text x="{535+i*230}" y="98" fill="{c["warm_white"]}" font-family="sans-serif" font-size="21">Section {i+1}</text>' for i in range(4))
    body = f'''<rect x="62" y="190" width="82" height="650" rx="40" fill="{c['charcoal']}" fill-opacity=".86"/>{pills}<rect x="190" y="180" width="1510" height="480" rx="30" fill="{c['charcoal']}" fill-opacity=".35"/><rect x="230" y="230" width="420" height="360" rx="22" fill="url(#art)"/><text x="710" y="300" fill="{c['champagne_gold']}" font-family="sans-serif" font-size="28">{svg_escape(family)}</text><text x="710" y="360" fill="{c['warm_white']}" font-family="sans-serif" font-size="52">Synthetic hero title</text><text x="710" y="420" fill="{c['soft_text']}" font-family="sans-serif" font-size="25">Privacy-safe fixture with text-safe hero area</text>{''.join(tiles)}'''
    return svg_frame(f'{family} page · {page["status"]}', body, tokens)


def games_tile(x: int, label: str, tokens: dict, *, focused: bool = False,
               missing: bool = False, status: str = "") -> str:
    c = tokens["colors"]
    title_y = 958
    focus = (
        f'<path d="M{x-4} 650 V930 M{x-4} 650 H{x+214} M{x+214} 650 V930" '
        f'stroke="{c["jade"]}" stroke-width="4" fill="none"/>'
        f'<rect x="{x-4}" y="926" width="218" height="64" rx="18" fill="{c["jade"]}"/>'
    ) if focused else ""
    if missing:
        art = (
            f'<rect x="{x}" y="654" width="210" height="276" rx="18" fill="{c["charcoal"]}"/>'
            f'<circle cx="{x+105}" cy="770" r="54" fill="{c["jade"]}"/>'
            f'<text x="{x+105}" y="786" text-anchor="middle" fill="{c["warm_white"]}" '
            f'font-family="sans-serif" font-size="42">PX</text>'
        )
    else:
        art = (
            f'<rect x="{x}" y="654" width="210" height="276" rx="18" fill="url(#art)"/>'
            f'<path d="M{x+20} 860 C{x+70} 790 {x+138} 900 {x+190} 800 V912 H{x+20} Z" '
            f'fill="{c["ink"]}" fill-opacity=".52"/>'
        )
    badge = (
        f'<rect x="{x+18}" y="674" width="112" height="34" rx="17" fill="{c["charcoal"]}"/>'
        f'<text x="{x+74}" y="697" text-anchor="middle" fill="{c["champagne_gold"]}" '
        f'font-family="sans-serif" font-size="16">{svg_escape(status)}</text>'
    ) if status else ""
    return (
        f'<g>{art}{badge}{focus}<text x="{x+8}" y="{title_y}" fill="{c["warm_white"] if focused else c["ink"]}" '
        f'font-family="sans-serif" font-size="22">{svg_escape(label)}</text></g>'
    )


def games_frame(title: str, body: str, tokens: dict) -> str:
    c = tokens["colors"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img" aria-label="{svg_escape(title)}">
<defs><linearGradient id="page" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#302820"/><stop offset=".42" stop-color="{c['charcoal']}"/><stop offset="1" stop-color="{c['warm_white']}"/></linearGradient><linearGradient id="art" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c['jade']}"/><stop offset="1" stop-color="{c['champagne_gold']}"/></linearGradient></defs>
<rect width="1920" height="1080" fill="url(#page)"/>{body}<text x="1840" y="1044" text-anchor="end" fill="{c['charcoal']}" font-family="sans-serif" font-size="16">AsterTV design candidate · synthetic</text></svg>'''


def games_page_render(page: dict, tokens: dict, state: str) -> str:
    c = tokens["colors"]
    filters = ("Library", "Continue", "Platforms", "Requests")
    filter_nodes = []
    for index, label in enumerate(filters):
        x = 450 + index * 228
        current = label == "Library"
        filter_nodes.append(
            f'<rect x="{x}" y="60" width="204" height="56" rx="28" fill="{c["charcoal"]}" '
            f'stroke="{c["champagne_gold"]}" stroke-width="{4 if current else 2}"/>'
            f'<text x="{x+102}" y="96" text-anchor="middle" fill="{c["warm_white"]}" '
            f'font-family="sans-serif" font-size="21">{label}</text>'
        )
    rail = (
        f'<rect x="62" y="188" width="82" height="650" rx="40" fill="{c["charcoal"]}" fill-opacity=".9"/>'
        f'<circle cx="103" cy="245" r="20" fill="{c["champagne_gold"]}"/>'
        f'<circle cx="103" cy="324" r="20" fill="{c["stone"]}"/>'
        f'<circle cx="103" cy="403" r="20" fill="{c["stone"]}"/>'
        f'<circle cx="103" cy="759" r="20" fill="{c["stone"]}"/>'
    )
    if state == "service-offline":
        body = rail + "".join(filter_nodes) + (
            f'<rect x="360" y="260" width="1200" height="560" rx="34" fill="{c["charcoal"]}" fill-opacity=".94"/>'
            f'<text x="960" y="420" text-anchor="middle" fill="{c["warm_white"]}" font-family="sans-serif" font-size="48">Games is taking a break</text>'
            f'<text x="960" y="478" text-anchor="middle" fill="{c["soft_text"]}" font-family="sans-serif" font-size="26">Your other AsterTV pages still work. Try the private game library again.</text>'
            f'<rect x="680" y="570" width="250" height="62" rx="28" fill="{c["jade"]}" stroke="{c["champagne_gold"]}" stroke-width="4"/>'
            f'<text x="805" y="610" text-anchor="middle" fill="{c["warm_white"]}" font-family="sans-serif" font-size="24">Try again</text>'
            f'<rect x="960" y="570" width="280" height="62" rx="28" fill="{c["charcoal"]}" stroke="{c["champagne_gold"]}" stroke-width="2"/>'
            f'<text x="1100" y="610" text-anchor="middle" fill="{c["warm_white"]}" font-family="sans-serif" font-size="24">Back to Home</text>'
        )
        return games_frame(f'Games · offline · {page["status"]}', body, tokens)
    if state == "empty-library":
        body = rail + "".join(filter_nodes) + (
            f'<rect x="184" y="164" width="1648" height="420" rx="30" fill="{c["charcoal"]}" fill-opacity=".72"/>'
            f'<text x="250" y="300" fill="{c["champagne_gold"]}" font-family="sans-serif" font-size="26">GAMES</text>'
            f'<text x="250" y="372" fill="{c["warm_white"]}" font-family="sans-serif" font-size="52">Your library is ready for its first game</text>'
            f'<text x="250" y="430" fill="{c["soft_text"]}" font-family="sans-serif" font-size="25">Browse a platform or send a request. Nothing is downloaded automatically.</text>'
            f'<rect x="250" y="478" width="290" height="62" rx="28" fill="{c["jade"]}" stroke="{c["champagne_gold"]}" stroke-width="4"/>'
            f'<text x="395" y="518" text-anchor="middle" fill="{c["warm_white"]}" font-family="sans-serif" font-size="24">Browse platforms</text>'
            f'<text x="184" y="642" fill="{c["ink"]}" font-family="sans-serif" font-size="30">Platforms</text>'
            + games_tile(184, "8-bit", tokens, focused=True, missing=True)
            + games_tile(424, "16-bit", tokens, missing=True)
            + games_tile(664, "Handheld", tokens, missing=True)
        )
        return games_frame(f'Games · empty library · {page["status"]}', body, tokens)

    hero_title = "The Remarkably Long Voyage Through Clockwork Caverns" if state == "long-title" else "Star Harbor"
    hero_title_svg = (
        f'<text x="250" y="308" fill="{c["warm_white"]}" font-family="sans-serif" font-size="48">The Remarkably Long Voyage</text>'
        f'<text x="250" y="362" fill="{c["warm_white"]}" font-family="sans-serif" font-size="48">Through Clockwork Caverns</text>'
    ) if state == "long-title" else (
        f'<text x="250" y="330" fill="{c["warm_white"]}" font-family="sans-serif" font-size="54">{hero_title}</text>'
    )
    hero = (
        f'<rect x="184" y="164" width="1648" height="420" rx="30" fill="{c["charcoal"]}" fill-opacity=".72"/>'
        f'<text x="250" y="244" fill="{c["champagne_gold"]}" font-family="sans-serif" font-size="24">CONTINUE PLAYING · 8-BIT</text>'
        + hero_title_svg +
        f'<text x="250" y="404" fill="{c["soft_text"]}" font-family="sans-serif" font-size="24">Resume from the lighthouse · save synced</text>'
        f'<rect x="250" y="458" width="220" height="62" rx="28" fill="{c["jade"]}" stroke="{c["champagne_gold"]}" stroke-width="4"/>'
        f'<text x="360" y="498" text-anchor="middle" fill="{c["warm_white"]}" font-family="sans-serif" font-size="24">Resume</text>'
        f'<rect x="494" y="458" width="220" height="62" rx="28" fill="{c["charcoal"]}" stroke="{c["champagne_gold"]}" stroke-width="2"/>'
        f'<text x="604" y="498" text-anchor="middle" fill="{c["warm_white"]}" font-family="sans-serif" font-size="24">Details</text>'
        f'<rect x="1296" y="208" width="242" height="322" rx="22" fill="url(#art)" transform="rotate(-7 1417 369)"/>'
        f'<rect x="1460" y="222" width="242" height="322" rx="22" fill="{c["jade"]}" transform="rotate(6 1581 383)"/>'
        f'<path d="M1330 470 C1430 380 1530 520 1680 330 V530 H1330 Z" fill="{c["ink"]}" fill-opacity=".45"/>'
    )
    names = ["Star Harbor", "Moss Circuit", "Parcel Knight", "Orbit Garden", "Pixel Crossing", "Lumen Rally", "Quiet Quest"]
    tiles = []
    for index, name in enumerate(names):
        label = "The Remarkably Long Voyage…" if state == "long-title" and index == 1 else name
        tiles.append(games_tile(184 + index * 232, label, tokens,
                                focused=(state == "focus" and index == 1),
                                missing=(state == "missing-art" and index == 3),
                                status="READY" if index in {0, 1} else ""))
    body = (
        rail + "".join(filter_nodes) + hero
        + f'<text x="184" y="638" fill="{c["ink"]}" font-family="sans-serif" font-size="30">Continue playing</text>'
        + "".join(tiles)
        + f'<text x="1738" y="1020" text-anchor="end" fill="{c["charcoal"]}" font-family="sans-serif" font-size="18">Design fixture · {svg_escape(state)}</text>'
    )
    return games_frame(f'Games · {state} · {page["status"]}', body, tokens)


def games_detail_render(page: dict, tokens: dict) -> str:
    c = tokens["colors"]
    actions = (("Play", True), ("Start new", False), ("Manage saves", False), ("Remove", False))
    buttons = []
    for index, (label, focused) in enumerate(actions):
        x = 650 + index * 250
        buttons.append(
            f'<rect x="{x}" y="520" width="224" height="60" rx="28" fill="{c["jade"] if focused else c["charcoal"]}" '
            f'stroke="{c["champagne_gold"]}" stroke-width="{4 if focused else 2}"/>'
            f'<text x="{x+112}" y="558" text-anchor="middle" fill="{c["warm_white"]}" font-family="sans-serif" font-size="22">{label}</text>'
        )
    body = (
        f'<rect x="72" y="54" width="1776" height="972" rx="34" fill="{c["charcoal"]}" fill-opacity=".78"/>'
        f'<text x="118" y="112" fill="{c["champagne_gold"]}" font-family="sans-serif" font-size="22">BACK TO GAMES</text>'
        f'<rect x="150" y="190" width="390" height="570" rx="24" fill="url(#art)"/>'
        f'<text x="650" y="250" fill="{c["champagne_gold"]}" font-family="sans-serif" font-size="24">8-BIT · READY ON THIS TV</text>'
        f'<text x="650" y="320" fill="{c["warm_white"]}" font-family="sans-serif" font-size="56">Star Harbor</text>'
        f'<text x="650" y="376" fill="{c["soft_text"]}" font-family="sans-serif" font-size="24">Sail between quiet islands, restore old beacons, and find a way home.</text>'
        f'<text x="650" y="430" fill="{c["soft_text"]}" font-family="sans-serif" font-size="21">1 player · controller ready · save synced moments ago</text>'
        + "".join(buttons)
        + f'<rect x="650" y="640" width="1050" height="260" rx="24" fill="{c["ink"]}" fill-opacity=".46"/>'
        f'<text x="692" y="700" fill="{c["champagne_gold"]}" font-family="sans-serif" font-size="22">ABOUT THIS GAME</text>'
        f'<text x="692" y="752" fill="{c["warm_white"]}" font-family="sans-serif" font-size="24">Verified library copy · local install 2.4 MiB</text>'
        f'<text x="692" y="800" fill="{c["soft_text"]}" font-family="sans-serif" font-size="22">Last played yesterday · progress belongs to this profile</text>'
    )
    return games_frame(f'Game detail · {page["status"]}', body, tokens)


def games_dialog_render(page: dict, tokens: dict, kind: str) -> str:
    c = tokens["colors"]
    content = {
        "install": ("Install on this TV?", "Verified source · 2.4 MiB required · 86 GiB free", ("Install", "Cancel")),
        "request": ("Request this game?", "The request will be pending. Nothing is approved automatically.", ("Send request", "Cancel")),
        "save-conflict": ("Choose which save to keep", "Local: today 18:42 · Server: today 18:37 · neither copy is deleted yet", ("Keep local", "Keep server", "Cancel")),
    }[kind]
    button_width = 230
    total = len(content[2]) * button_width + (len(content[2]) - 1) * 24
    start = 960 - total // 2
    buttons = []
    for index, label in enumerate(content[2]):
        x = start + index * (button_width + 24)
        focused = (kind != "save-conflict" and index == 0) or (kind == "save-conflict" and label == "Cancel")
        buttons.append(
            f'<rect x="{x}" y="650" width="{button_width}" height="62" rx="28" fill="{c["jade"] if focused else c["charcoal"]}" '
            f'stroke="{c["champagne_gold"]}" stroke-width="{4 if focused else 2}"/>'
            f'<text x="{x+button_width//2}" y="690" text-anchor="middle" fill="{c["warm_white"]}" font-family="sans-serif" font-size="22">{label}</text>'
        )
    body = (
        f'<rect width="1920" height="1080" fill="{c["ink"]}" fill-opacity=".64"/>'
        f'<rect x="400" y="260" width="1120" height="520" rx="34" fill="{c["charcoal"]}" stroke="{c["champagne_gold"]}" stroke-width="2"/>'
        f'<text x="960" y="392" text-anchor="middle" fill="{c["warm_white"]}" font-family="sans-serif" font-size="46">{svg_escape(content[0])}</text>'
        f'<text x="960" y="470" text-anchor="middle" fill="{c["soft_text"]}" font-family="sans-serif" font-size="23">{svg_escape(content[1])}</text>'
        f'<text x="960" y="548" text-anchor="middle" fill="{c["champagne_gold"]}" font-family="sans-serif" font-size="20">Star Harbor · 8-bit</text>'
        + "".join(buttons)
    )
    return games_frame(f'Games {kind} dialog · {page["status"]}', body, tokens)


def news_player_render(page: dict, tokens: dict) -> str:
    c = tokens["colors"]
    stories = [
        ("Harbour restores its night ferry", "Coastline Journal", "00:00", "#365B50", False),
        ("Library opens a living archive", "Civic Review", "03:18", "#9B7048", True),
        ("Orchestra returns to the square", "Arts Desk", "06:42", "#5E4F6B", False),
        ("New trail links the valley", "Field Notes", "09:11", "#476070", False),
        ("Morning markets find new growers", "Regional Wire", "12:27", "#7A5948", False),
    ]
    rows = []
    for index, (title, source, clock, art, active) in enumerate(stories):
        y = 238 + index * 142
        fill = c["charcoal"] if not active else "#493D28"
        stroke = c["champagne_gold"] if active else "#00000000"
        rows.append(
            f'<g><rect x="1050" y="{y}" width="770" height="126" rx="18" fill="{fill}" fill-opacity=".88" stroke="{stroke}" stroke-width="{4 if active else 0}"/>'
            f'<rect x="1062" y="{y+10}" width="184" height="106" rx="12" fill="{art}"/>'
            f'<text x="1270" y="{y+42}" fill="{c["warm_white"]}" font-family="sans-serif" font-size="24">{svg_escape(title)}</text>'
            f'<text x="1270" y="{y+82}" fill="{c["champagne_gold"] if active else c["soft_text"]}" font-family="sans-serif" font-size="18">{svg_escape(source)} · {clock}</text>'
            f'<text x="1770" y="{y+82}" fill="{c["champagne_gold"]}" font-family="sans-serif" font-size="17">{"PLAYING" if active else ""}</text></g>'
        )
    controls = []
    glyphs = {
        "Previous": '<path d="M45 17 L25 29 L45 41 Z M20 16 V42"/>',
        "Pause": '<rect x="24" y="16" width="7" height="26" rx="2"/><rect x="39" y="16" width="7" height="26" rx="2"/>',
        "Next": '<path d="M25 17 L45 29 L25 41 Z M50 16 V42"/>',
        "Stop": '<rect x="24" y="17" width="24" height="24" rx="4"/>',
    }
    for index, label in enumerate(("Previous", "Pause", "Next", "Stop")):
        x = 150 + index * 126
        controls.append(
            f'<g transform="translate({x} 900)" fill="{c["warm_white"]}" stroke="{c["warm_white"]}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">'
            f'<title>{label}</title><rect width="82" height="58" rx="24" fill="{c["jade"] if label == "Pause" else c["charcoal"]}" stroke="{c["champagne_gold"]}" stroke-width="{4 if label == "Pause" else 2}"/>{glyphs[label]}</g>'
        )
    body = (
        f'<rect x="70" y="165" width="900" height="810" rx="30" fill="{c["charcoal"]}" fill-opacity=".66"/>'
        f'<rect x="1025" y="165" width="825" height="810" rx="30" fill="{c["charcoal"]}" fill-opacity=".42"/>'
        f'<rect x="112" y="220" width="816" height="382" rx="22" fill="#9B7048"/>'
        f'<path d="M112 520 C350 410 600 640 928 420 L928 602 L112 602 Z" fill="#1D352D" fill-opacity=".72"/>'
        f'<text x="112" y="658" fill="{c["champagne_gold"]}" font-family="sans-serif" font-size="22">NOW PLAYING · STORY 2 OF 5</text>'
        f'<text x="112" y="708" fill="{c["warm_white"]}" font-family="sans-serif" font-size="38">Library opens a living archive</text>'
        f'<text x="112" y="750" fill="{c["soft_text"]}" font-family="sans-serif" font-size="20">Civic Review · A new oral-history collection brings local voices together.</text>'
        f'<text x="112" y="824" fill="{c["warm_white"]}" font-family="sans-serif" font-size="19">04:12</text>'
        f'<text x="928" y="824" text-anchor="end" fill="{c["warm_white"]}" font-family="sans-serif" font-size="19">15:54</text>'
        f'<rect x="112" y="846" width="816" height="10" rx="5" fill="{c["soft_text"]}" fill-opacity=".32"/>'
        f'<rect x="112" y="846" width="216" height="10" rx="5" fill="{c["light_jade"]}"/>'
        + ''.join(controls)
        + f'<text x="1050" y="210" fill="{c["warm_white"]}" font-family="sans-serif" font-size="30">In this briefing</text>'
        + ''.join(rows)
        + f'<rect x="1665" y="72" width="150" height="52" rx="26" fill="{c["charcoal"]}" stroke="{c["champagne_gold"]}" stroke-width="2"/>'
        f'<text x="1740" y="105" text-anchor="middle" fill="{c["warm_white"]}" font-family="sans-serif" font-size="20">Back to News</text>'
    )
    return svg_frame(f'News player · {page["status"]}', body, tokens)


def render(tokens: dict, catalogue: dict, asset_index: dict) -> str:
    colors = tokens["colors"]
    component_sections = []
    for component in catalogue["components"]:
        chips = "".join(
            f'<span class="state {"focus" if state == "focus" else ""}">{html.escape(state)}</span>'
            for state in component["states"]
        )
        variants = " · ".join(html.escape(value) for value in component["variants"])
        component_sections.append(
            f'<section><h2>{html.escape(component["id"].replace("-", " ").title())}</h2>'
            f'<p>{variants}</p><div class="states">{chips}</div></section>'
        )
    pages = "".join(
        f'<li><strong>{html.escape(page["id"])}</strong><span>{html.escape(page["status"])}</span>'
        f'<small>{len(xml_controls(page.get("template", "")))} controls indexed'
        f'{" · design-only" if page.get("design_spec") else ""}</small></li>'
        for page in catalogue["pages"]
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AsterTV pattern library</title>
<style>
:root{{--ink:{colors['ink']};--charcoal:{colors['charcoal']};--cream:{colors['warm_white']};--soft:{colors['soft_text']};--gold:{colors['champagne_gold']};--jade:{colors['jade']};--light-jade:{colors['light_jade']};}}
*{{box-sizing:border-box}} body{{margin:0;background:linear-gradient(135deg,#302820 0%,var(--charcoal) 38%,var(--cream) 100%);color:var(--cream);font-family:system-ui,sans-serif;min-height:100vh;padding:48px}} header{{max-width:1100px;margin:auto auto 34px}} h1{{font-weight:400;font-size:40px;margin:0}} header p{{color:var(--soft);max-width:760px}} main{{max-width:1100px;margin:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:20px}} section{{background:rgba(23,28,25,.78);border-radius:22px;padding:20px;box-shadow:0 12px 30px rgba(0,0,0,.22),inset 0 1px rgba(255,255,255,.08)}} h2{{font-size:20px;font-weight:500;color:var(--gold);margin:0 0 8px}} section p{{min-height:42px;color:var(--soft);margin:0 0 14px}} .states{{display:flex;gap:8px;flex-wrap:wrap}} .state{{border:1px solid rgba(216,183,120,.6);border-radius:999px;padding:7px 12px;background:rgba(23,28,25,.82)}} .state.focus{{background:var(--jade);border-color:var(--gold);box-shadow:0 4px 12px rgba(0,0,0,.35),inset 0 1px rgba(255,255,255,.12)}} .pages{{grid-column:1/-1}} ul{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;list-style:none;padding:0;margin:0}} li{{display:grid;gap:3px;padding:12px 14px;border-left:3px solid var(--gold);background:rgba(23,28,25,.64)}} li span{{color:var(--light-jade)}} li small{{color:var(--soft)}} footer{{max-width:1100px;margin:28px auto 0;color:var(--charcoal)}} @media(max-width:760px){{body{{padding:24px}}main,ul{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>AsterTV design authority</h1><p>Deterministic synthetic reference. Rest and focus geometry are identical; jade communicates focus and champagne gold communicates structure or persistent context.</p></header><main>{''.join(component_sections)}<section class="pages"><h2>Mapped pages</h2><ul>{pages}</ul></section></main><footer>{len(asset_index['runtime_assets'])} runtime assets indexed by SHA-256 · generated from repository authority</footer></body></html>'''


def outputs() -> dict[Path, str]:
    tokens = load("tokens.json")
    catalogue = load("catalogue.json")
    policy = load("asset-policy.json")
    graphs = load("focus-graphs.json")
    focus_errors = validate_focus(graphs)
    if focus_errors:
        raise SystemExit("\n".join(focus_errors))
    records = runtime_assets()
    asset_errors = validate_asset_policy(catalogue, policy, records)
    if asset_errors:
        raise SystemExit("\n".join(asset_errors))
    asset_index = {
        "schema_version": 1,
        "asset_policy": policy,
        "source_releases": catalogue["asset_releases"],
        "semantic_assets": catalogue["semantic_assets"],
        "runtime_assets": records,
    }
    page_index = {
        "schema_version": 1,
        "pages": [dict(page, controls=xml_controls(page.get("template", ""))) for page in catalogue["pages"]],
        "unmapped_required_families": sorted(set(catalogue["required_page_families"]) - {p["family"] for p in catalogue["pages"]}),
    }
    rendered = {
        GENERATED / "asset-index.json": canonical(asset_index),
        GENERATED / "page-index.json": canonical(page_index),
        GENERATED / "pattern-library.html": render(tokens, catalogue, asset_index),
    }
    fixture_index = {"schema_version": 1, "fixtures": []}
    for component in catalogue["components"]:
        path = GENERATED / "renders/components" / f'{component["id"]}.svg'
        rendered[path] = component_render(component, tokens)
        fixture_index["fixtures"].append({"id": f'component-{component["id"]}', "kind": "component", "source": component["id"], "path": path.relative_to(HERE).as_posix(), "width": 1920, "height": 1080, "synthetic": True})
    for page in catalogue["pages"]:
        path = GENERATED / "renders/pages" / f'{page["id"]}.svg'
        if page["id"] == "games":
            rendered[path] = games_page_render(page, tokens, "rest")
            fixture_index["fixtures"].append({"id": "page-games-rest", "kind": "page", "source": "games", "state": "rest", "path": path.relative_to(HERE).as_posix(), "width": 1920, "height": 1080, "synthetic": True})
            for state in ("focus", "empty-library", "service-offline", "missing-art", "long-title"):
                variant = GENERATED / "renders/pages" / f"games-{state}.svg"
                rendered[variant] = games_page_render(page, tokens, state)
                fixture_index["fixtures"].append({"id": f"page-games-{state}", "kind": "page", "source": "games", "state": state, "path": variant.relative_to(HERE).as_posix(), "width": 1920, "height": 1080, "synthetic": True})
            detail = GENERATED / "renders/pages/game-detail.svg"
            rendered[detail] = games_detail_render(page, tokens)
            fixture_index["fixtures"].append({"id": "page-game-detail", "kind": "page", "source": "games", "state": "detail", "path": detail.relative_to(HERE).as_posix(), "width": 1920, "height": 1080, "synthetic": True})
            for dialog_kind in ("install", "request", "save-conflict"):
                dialog = GENERATED / "renders/pages" / f"game-{dialog_kind}-dialog.svg"
                rendered[dialog] = games_dialog_render(page, tokens, dialog_kind)
                fixture_index["fixtures"].append({"id": f"dialog-game-{dialog_kind}", "kind": "dialog", "source": "games", "state": dialog_kind, "path": dialog.relative_to(HERE).as_posix(), "width": 1920, "height": 1080, "synthetic": True})
        else:
            rendered[path] = news_player_render(page, tokens) if page["id"] == "news-player" else page_render(page, tokens)
            fixture_index["fixtures"].append({"id": f'page-{page["id"]}', "kind": "page", "source": page["id"], "path": path.relative_to(HERE).as_posix(), "width": 1920, "height": 1080, "synthetic": True})
    rendered[GENERATED / "fixture-index.json"] = canonical(fixture_index)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = outputs()
    stale = []
    for path, content in expected.items():
        if args.check:
            if not path.exists() or path.read_text() != content:
                stale.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    if stale:
        print("stale generated design outputs:")
        print("\n".join(stale))
        return 1
    print(f"AsterTV design outputs {'verified' if args.check else 'generated'}: {len(expected)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
