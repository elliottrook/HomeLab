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


def xml_controls(template: str) -> list[int]:
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
    for index, label in enumerate(("Previous", "Pause", "Next", "Stop")):
        x = 122 + index * 148
        controls.append(
            f'<rect x="{x}" y="900" width="126" height="58" rx="28" fill="{c["jade"] if label == "Pause" else c["charcoal"]}" stroke="{c["champagne_gold"]}" stroke-width="{4 if label == "Pause" else 2}"/>'
            f'<text x="{x+63}" y="936" text-anchor="middle" fill="{c["warm_white"]}" font-family="sans-serif" font-size="19">{label}</text>'
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
        f'<small>{len(xml_controls(page["template"]))} controls indexed</small></li>'
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
    graphs = load("focus-graphs.json")
    focus_errors = validate_focus(graphs)
    if focus_errors:
        raise SystemExit("\n".join(focus_errors))
    asset_index = {
        "schema_version": 1,
        "source_releases": catalogue["asset_releases"],
        "semantic_assets": catalogue["semantic_assets"],
        "runtime_assets": runtime_assets(),
    }
    page_index = {
        "schema_version": 1,
        "pages": [dict(page, controls=xml_controls(page["template"])) for page in catalogue["pages"]],
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
