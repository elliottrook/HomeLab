"""Read-only recommendation portal for the shadow stack."""

from __future__ import annotations

import html
import json
import os
import hashlib
import secrets
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.parse import urlparse

from trakt_oauth import (begin_device, begin_pkce, exchange_code, poll_device,
                         write_secret)


SNAPSHOT_PATH = Path(os.environ.get("PORTAL_SNAPSHOT_PATH", "/data/recommendations.json"))
STATE_PATH = Path(os.environ.get("PORTAL_STATE_PATH", "/state/actions.json"))
ACTION_ENABLED = os.environ.get("PORTAL_ACTIONS_ENABLED", "NO") == "YES"
ASSET_DIR = Path(__file__).with_name("assets")
STATIC_ASSETS = {
    "/favicon.png": ("icon-32.png", "image/png"),
    "/icon-32.png": ("icon-32.png", "image/png"),
    "/icon-180.png": ("icon-180.png", "image/png"),
    "/icon-512.png": ("icon-512.png", "image/png"),
    "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json"),
}
TRAKT_CLIENT_ID_PATH = os.environ.get("TRAKT_CLIENT_ID_PATH", "/run/unified-secrets/trakt-client-id")
TRAKT_ACCESS_TOKEN_PATH = os.environ.get("TRAKT_ACCESS_TOKEN_PATH", "/run/unified-secrets/trakt-access-token")
TRAKT_REFRESH_TOKEN_PATH = os.environ.get("TRAKT_REFRESH_TOKEN_PATH", "/run/unified-secrets/trakt-refresh-token")
TRAKT_OAUTH_STATE_PATH = Path(os.environ.get("TRAKT_OAUTH_STATE_PATH", "/state/trakt-oauth.json"))
TRAKT_DEVICE_STATE_PATH = Path(os.environ.get("TRAKT_DEVICE_STATE_PATH", "/state/trakt-device.json"))
TRAKT_REDIRECT_URI = os.environ.get("TRAKT_REDIRECT_URI", "https://recommendations.elliottrook.com/oauth/trakt/callback")


def load_recommendations() -> list[dict[str, Any]]:
    if not SNAPSHOT_PATH.exists():
        return []
    with SNAPSHOT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("recommendation snapshot must be a JSON list")
    return [item for item in payload if isinstance(item, dict)]


def _trakt_connect_url() -> str:
    client_id = Path(TRAKT_CLIENT_ID_PATH).read_text(encoding="utf-8").strip()
    if not client_id:
        raise RuntimeError("Trakt client ID is not configured")
    state, pending = begin_pkce(client_id, TRAKT_REDIRECT_URI)
    TRAKT_OAUTH_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRAKT_OAUTH_STATE_PATH.write_text(json.dumps({"state": state, "verifier": pending["verifier"]}), encoding="utf-8")
    TRAKT_OAUTH_STATE_PATH.chmod(0o600)
    return pending["url"]


def _trakt_callback(query: Mapping[str, list[str]]) -> str:
    state = (query.get("state") or [""])[0]
    code = (query.get("code") or [""])[0]
    if not state or not code or not TRAKT_OAUTH_STATE_PATH.exists():
        raise RuntimeError("Trakt authorization response is incomplete")
    pending = json.loads(TRAKT_OAUTH_STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(pending, Mapping) or not secrets.compare_digest(state, str(pending.get("state", ""))):
        raise RuntimeError("Trakt authorization state did not match")
    client_id = Path(TRAKT_CLIENT_ID_PATH).read_text(encoding="utf-8").strip()
    payload = exchange_code(client_id=client_id, code=code,
                            verifier=str(pending["verifier"]), redirect_uri=TRAKT_REDIRECT_URI)
    write_secret(TRAKT_ACCESS_TOKEN_PATH, str(payload["access_token"]))
    write_secret(TRAKT_REFRESH_TOKEN_PATH, str(payload["refresh_token"]))
    TRAKT_OAUTH_STATE_PATH.unlink(missing_ok=True)
    return "Trakt connected. You may close this tab."


def _trakt_device_start() -> dict[str, Any]:
    client_id = Path(TRAKT_CLIENT_ID_PATH).read_text(encoding="utf-8").strip()
    payload = begin_device(client_id)
    TRAKT_DEVICE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRAKT_DEVICE_STATE_PATH.write_text(json.dumps({
        "device_code": payload["device_code"], "client_id": client_id,
        "user_code": payload.get("user_code", ""),
        "verification_url": payload.get("verification_url", "https://trakt.tv/activate"),
        "expires_in": payload.get("expires_in", 600),
    }), encoding="utf-8")
    TRAKT_DEVICE_STATE_PATH.chmod(0o600)
    return payload


def _trakt_device_status() -> str:
    if not TRAKT_DEVICE_STATE_PATH.exists():
        return "not_started"
    pending = json.loads(TRAKT_DEVICE_STATE_PATH.read_text(encoding="utf-8"))
    result = poll_device(client_id=str(pending["client_id"]),
                         device_code=str(pending["device_code"]))
    if result.get("error"):
        return str(result["error"])
    write_secret(TRAKT_ACCESS_TOKEN_PATH, str(result["access_token"]))
    write_secret(TRAKT_REFRESH_TOKEN_PATH, str(result["refresh_token"]))
    TRAKT_DEVICE_STATE_PATH.unlink(missing_ok=True)
    return "connected"


def _display_type(media_type: Any) -> str:
    return {"movie": "Film", "tv": "TV", "album": "Music album",
            "ebook": "Ebook", "audiobook": "Audiobook"}.get(str(media_type), str(media_type).title())


def _poster_url(item: Mapping[str, Any]) -> str:
    poster = str(item.get("poster_path", ""))
    if poster.startswith("http://") or poster.startswith("https://"):
        return poster
    if poster.startswith("/"):
        return "https://image.tmdb.org/t/p/w500" + poster
    return ""


def _source_url(item: Mapping[str, Any]) -> str:
    """Return a read-only source page for the item's authority identity."""
    configured = str(item.get("source_url", "")).strip()
    if configured.startswith("https://"):
        return configured
    authority = str(item.get("authority", ""))
    media_type = str(item.get("media_type", ""))
    authority_id = str(item.get("authority_id", "")).strip()
    if not authority_id:
        return ""
    if authority == "seerr" and media_type in {"movie", "tv"} and authority_id.isdigit():
        return f"https://www.themoviedb.org/{media_type}/{urllib.parse.quote(authority_id, safe='')}"
    if authority == "openlibrary":
        key = authority_id if authority_id.startswith("/") else f"/works/{authority_id}"
        return "https://openlibrary.org" + urllib.parse.quote(key, safe="/")
    if authority == "musicbrainz":
        return f"https://musicbrainz.org/release-group/{urllib.parse.quote(authority_id, safe='')}"
    return ""


def render_html(items: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    cards = []
    for item in items:
        kind = str(item.get("media_type", "unknown"))
        counts[kind] = counts.get(kind, 0) + 1
        title = html.escape(str(item.get("title", "Untitled")))
        display_type = html.escape(_display_type(kind))
        explanation = html.escape(str(item.get("explanation") or "No explanation was provided."))
        overview = html.escape(str(item.get("overview") or "No synopsis is available yet."))
        creator = item.get("artist") or item.get("author")
        creator_label = "Artist" if item.get("artist") else "Author"
        creator_html = (f"<p class='creator'><strong>{creator_label}</strong> "
                        f"{html.escape(str(creator))}</p>" if creator else "")
        year = html.escape(str(item.get("year", "")))
        rating = item.get("rating")
        rating_text = html.escape(f"{float(rating):.1f}/10" if isinstance(rating, (int, float)) else "")
        genres = item.get("genres") if isinstance(item.get("genres"), list) else []
        genre_text = html.escape(" · ".join(str(value) for value in genres[:3]))
        poster = _poster_url(item)
        source_url = _source_url(item)
        poster_image = (f"<img class='poster' src='{html.escape(poster, quote=True)}' alt='{title} artwork' loading='lazy'>"
                       if poster else "<div class='poster poster-fallback' aria-label='Artwork unavailable'>✦</div>")
        poster_html = (f"<a class='poster-link' href='{html.escape(source_url, quote=True)}' target='_blank' rel='noopener noreferrer' aria-label='Open {title} source page'>{poster_image}</a>"
                       if source_url else poster_image)
        metadata = " · ".join(value for value in (year, rating_text, genre_text) if value)
        source = html.escape(str(item.get("source_label") or item.get("authority", "")))
        eligible = not item.get("owned") and not item.get("archived") and item.get("match_count", 1) == 1
        if eligible:
            authority = html.escape(str(item.get("authority", "")), quote=True)
            authority_id = html.escape(str(item.get("authority_id", "")), quote=True)
            raw_title = html.escape(str(item.get("title", "")), quote=True)
            action = (
                f"<button type='button' class='request-button' data-authority='{authority}' "
                f"data-authority-id='{authority_id}' data-title='{raw_title}'>Request this {display_type.lower()}</button>"
            )
            status = "<span class='status status-ready'>Ready for your approval</span>"
        else:
            action = "<button type='button' class='request-button' disabled>Unavailable</button>"
            status = "<span class='status'>Already owned, archived, or ambiguous</span>"
        source_link = (f"<a class='source-link' href='{html.escape(source_url, quote=True)}' target='_blank' rel='noopener noreferrer'>Open source page ↗</a>"
                       if source_url else "")
        cards.append(
            f"<article class='card' data-type='{html.escape(kind, quote=True)}'>"
            f"{poster_html}<div class='card-content'><div class='eyebrow'>{display_type}"
            f"<span class='source'>{source}</span></div><h2>{title}</h2>"
            f"<p class='metadata'>{metadata}</p>{creator_html}<p class='overview'>{overview}</p>"
            f"<div class='why'><strong>Why this is here</strong><p>{explanation}</p></div>{source_link}"
            f"<div class='card-footer'>{status}{action}<span class='result' role='status'></span></div>"
            f"</div></article>"
        )
    buttons = ["<button class='filter active' data-filter='all'>All <span>%d</span></button>" % len(items)]
    for kind, count in sorted(counts.items()):
        buttons.append(f"<button class='filter' data-filter='{html.escape(kind, quote=True)}'>{html.escape(_display_type(kind))} <span>{count}</span></button>")
    body = "\n".join(cards) or "<div class='empty'><h2>No safe recommendations yet</h2><p>The refresh service has not produced any candidates. Check its health before requesting anything.</p></div>"
    refreshed = "Unknown"
    try:
        refreshed = datetime.fromtimestamp(SNAPSHOT_PATH.stat().st_mtime, timezone.utc).astimezone().strftime("%b %-d, %Y at %-I:%M %p")
    except OSError:
        pass
    script = """
<script>
const search = document.querySelector('#search');
const filters = document.querySelectorAll('.filter');
const cards = document.querySelectorAll('.card');
function applyFilters() {
  const selected = document.querySelector('.filter.active').dataset.filter;
  const query = search ? search.value.trim().toLowerCase() : '';
  cards.forEach((card) => {
    const matchesType = selected === 'all' || card.dataset.type === selected;
    const matchesSearch = !query || card.dataset.search.includes(query);
    card.hidden = !matchesType || !matchesSearch;
  });
}
if (search) search.addEventListener('input', applyFilters);
const searchType = document.querySelector('#search-type');
const searchButton = document.querySelector('#search-submit');
const searchResults = document.querySelector('#search-results');
function escapeHtml(value) { const node = document.createElement('div'); node.textContent = value || ''; return node.innerHTML; }
async function runProviderSearch() {
  const query = search.value.trim();
  if (!query) { searchResults.hidden = true; searchResults.innerHTML = ''; return; }
  searchButton.disabled = true; searchButton.textContent = 'Searching…';
  try {
    const response = await fetch('/api/search?q=' + encodeURIComponent(query) + '&type=' + encodeURIComponent(searchType.value));
    const results = await response.json();
    if (!response.ok) throw new Error(results.error || 'Search failed');
    searchResults.innerHTML = results.length ? results.map(item => {
      const poster = item.poster_path ? `<img class='search-poster' src='${escapeHtml(item.poster_path)}' alt='' loading='lazy'>` : `<div class='search-poster poster-fallback'>✦</div>`;
      const creator = item.artist || item.author ? `<div class='creator'>${escapeHtml(item.artist || item.author)}</div>` : '';
      const source = item.source_url ? `<a class='source-link' href='${escapeHtml(item.source_url)}' target='_blank' rel='noopener noreferrer'>Open source ↗</a>` : '';
      return `<article class='search-card'>${poster}<div><div class='eyebrow'>${escapeHtml(item.media_type)} <span class='source'>${escapeHtml(item.source_label)}</span></div><h2>${escapeHtml(item.title)}</h2><p class='metadata'>${escapeHtml(item.year || '')}</p>${creator}<p class='overview'>${escapeHtml(item.overview || 'No synopsis available.')}</p>${source}</div></article>`;
    }).join('') : `<div class='empty'>No results found across the selected sources.</div>`;
    searchResults.hidden = false;
  } catch (error) { searchResults.innerHTML = `<div class='empty error'>${escapeHtml(error.message)}</div>`; searchResults.hidden = false; }
  searchButton.disabled = false; searchButton.textContent = 'Search all media';
}
if (searchButton) searchButton.addEventListener('click', runProviderSearch);
if (search) search.addEventListener('keydown', (event) => { if (event.key === 'Enter') runProviderSearch(); });
filters.forEach((filter) => filter.addEventListener('click', () => {
  filters.forEach((item) => item.classList.remove('active'));
  filter.classList.add('active');
  applyFilters();
}));
document.querySelectorAll('.request-button:not([disabled])').forEach((button) => {
  button.addEventListener('click', async () => {
    const result = button.parentElement.querySelector('.result');
    button.disabled = true;
    button.textContent = 'Submitting…';
    result.textContent = '';
    try {
      const response = await fetch('/api/request', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({approve: true, authority: button.dataset.authority,
          authority_id: button.dataset.authorityId, title: button.dataset.title})
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.error || 'Request failed');
      button.textContent = 'Requested';
      result.textContent = 'Request sent.';
      result.className = 'result success';
    } catch (error) {
      button.disabled = false;
      button.textContent = 'Try again';
      result.textContent = error.message;
      result.className = 'result error';
    }
  });
});
</script>
"""
    style = """
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#151d31;--panel2:#1b2740;--text:#f4f7fb;--muted:#aab6ca;--accent:#8bd3ff;--accent2:#b9f2d0;--line:#2b3a58}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top right,#25395a 0,#0b1020 48%);color:var(--text);font:16px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1180px;margin:auto;padding:42px 24px 72px}header{display:flex;justify-content:space-between;gap:24px;align-items:end;margin-bottom:30px}.kicker,.eyebrow{color:var(--accent);font-size:.78rem;font-weight:750;letter-spacing:.12em;text-transform:uppercase}.kicker{margin-bottom:10px}h1{font-size:clamp(2.2rem,6vw,4.5rem);line-height:1.02;margin:0;letter-spacing:-.05em}header p{max-width:560px;color:var(--muted);margin:.9rem 0 0}.toolbar{display:flex;align-items:center;gap:12px;margin:0 0 14px}.toolbar label{font-size:.8rem;color:var(--muted);white-space:nowrap}.toolbar input{width:min(520px,100%);border:1px solid var(--line);border-radius:10px;background:#111a2c;color:var(--text);font:inherit;padding:10px 13px}.toolbar select{border:1px solid var(--line);border-radius:10px;background:#111a2c;color:var(--text);font:inherit;padding:10px 13px}.search-results{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin:0 0 24px}.search-card{display:grid;grid-template-columns:82px 1fr;gap:14px;background:linear-gradient(145deg,var(--panel),#10182a);border:1px solid var(--line);border-radius:14px;padding:12px}.search-poster{width:82px;height:122px;border-radius:8px;object-fit:cover;background:#263653}.search-card h2{font-size:1.05rem;margin:.3rem 0}.refreshed{margin-left:auto;color:var(--muted);font-size:.76rem}.filters{display:flex;flex-wrap:wrap;gap:10px;padding:14px;background:#111a2c;border:1px solid var(--line);border-radius:16px;margin-bottom:24px}.filter{border:1px solid var(--line);background:transparent;color:var(--muted);border-radius:999px;padding:9px 15px;font:inherit;cursor:pointer}.filter.active,.filter:hover{background:var(--accent);color:#07111d;border-color:var(--accent)}.filter span{font-size:.8em;opacity:.75}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px}.card{display:grid;grid-template-columns:116px 1fr;gap:18px;background:linear-gradient(145deg,var(--panel),#10182a);border:1px solid var(--line);border-radius:18px;padding:14px;box-shadow:0 12px 30px #0003}.poster-link{display:block;text-decoration:none}.poster-link:focus-visible{outline:2px solid var(--accent);outline-offset:3px}.poster{width:116px;height:174px;border-radius:11px;object-fit:cover;background:#263653}.poster-fallback{display:grid;place-items:center;font-size:2.5rem;color:var(--accent)}.card-content{min-width:0}.source{float:right;color:var(--muted);font-size:.72rem;letter-spacing:0;text-transform:none}.source-link{display:inline-block;color:var(--accent);font-size:.78rem;margin-top:10px;text-decoration:none}.source-link:hover{text-decoration:underline}.card h2{font-size:1.35rem;line-height:1.12;margin:.5rem 0 .2rem}.metadata{color:var(--muted);font-size:.82rem;min-height:1.25em;margin:0 0 .8rem}.creator{color:#dce4f1;font-size:.84rem;margin:.25rem 0 .65rem}.creator strong{color:var(--accent2);font-weight:700}.overview{color:#dce4f1;font-size:.9rem;margin:.4rem 0 1rem;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}.why{border-left:3px solid var(--accent);padding-left:10px;color:var(--muted);font-size:.82rem}.why strong{color:var(--accent2)}.why p{margin:.2rem 0}.card-footer{display:flex;flex-wrap:wrap;align-items:center;gap:9px;margin-top:18px}.request-button{border:0;border-radius:10px;background:var(--accent);color:#07111d;font:700 .9rem system-ui;padding:10px 13px;cursor:pointer}.request-button:hover{filter:brightness(1.08)}.request-button:disabled{background:#44516a;color:#c1cada;cursor:not-allowed}.status{font-size:.72rem;color:var(--muted);flex:1}.status-ready{color:var(--accent2)}.result{width:100%;font-size:.78rem}.success{color:var(--accent2)}.error{color:#ffaaa8}.empty{padding:50px;border:1px dashed var(--line);border-radius:18px;color:var(--muted)}footer{color:var(--muted);font-size:.8rem;margin-top:28px}@media(max-width:600px){main{padding:26px 14px 50px}header{display:block}.toolbar{display:block}.toolbar label{display:block;margin-bottom:6px}.refreshed{display:block;margin:8px 0}.grid{display:block}.card{margin-bottom:16px}.card h2{font-size:1.2rem}}
</style>
"""
    style = style.replace('.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px}.card{display:grid;', '.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px}.card[hidden]{display:none}.card{display:grid;')
    style = style.replace('.toolbar{display:flex;', '.page-nav{display:flex;gap:10px;margin-bottom:26px}.page-pill{border:1px solid var(--line);border-radius:999px;padding:9px 16px;color:var(--muted);text-decoration:none}.page-pill.active,.page-pill:hover{background:var(--accent);color:#07111d;border-color:var(--accent)}.toolbar{display:flex;')
    for item, card in zip(items, cards):
        search_value = html.escape(" ".join(str(item.get(key, "")) for key in ("title", "overview", "explanation")).casefold(), quote=True)
        cards[cards.index(card)] = card.replace("<article class='card'", f"<article data-search='{search_value}' class='card'", 1)
    body = "\n".join(cards) or "<div class='empty'><h2>No safe recommendations yet</h2><p>The refresh service has not produced any candidates. Check its health before requesting anything.</p></div>"
    return "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><meta name='theme-color' content='#0b1020'><link rel='icon' type='image/png' sizes='32x32' href='/icon-32.png'><link rel='apple-touch-icon' sizes='180x180' href='/icon-180.png'><link rel='manifest' href='/manifest.webmanifest'><title>Unified Media Recommendations</title>" + style + "</head><body><main><nav class='page-nav' aria-label='Media portal pages'><a class='page-pill active' href='/'>Recommendations</a><a class='page-pill' href='/search'>Search</a></nav><header><div><div class='kicker'>Private media concierge</div><h1>What should we add next?</h1><p>Review a short, explainable list and approve only what you actually want. Nothing is acquired without your button press.</p></div></header><div class='refreshed'>Updated " + html.escape(refreshed) + "</div><nav class='filters' aria-label='Filter recommendations'>" + "".join(buttons) + "</nav><section class='grid' aria-live='polite'>" + body + "</section><footer>Sources are refreshed periodically. Search is read-only; requests remain explicit and go through the owning service.</footer></main>" + script + "</body></html>"


def render_search_html() -> str:
    style = """
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#151d31;--text:#f4f7fb;--muted:#aab6ca;--accent:#8bd3ff;--accent2:#b9f2d0;--line:#2b3a58}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top right,#25395a 0,#0b1020 48%);color:var(--text);font:16px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1180px;margin:auto;padding:42px 24px 72px}.page-nav{display:flex;gap:10px;margin-bottom:26px}.page-pill{border:1px solid var(--line);border-radius:999px;padding:9px 16px;color:var(--muted);text-decoration:none}.page-pill.active,.page-pill:hover{background:var(--accent);color:#07111d;border-color:var(--accent)}.kicker,.eyebrow{color:var(--accent);font-size:.78rem;font-weight:750;letter-spacing:.12em;text-transform:uppercase}.kicker{margin-bottom:10px}h1{font-size:clamp(2.2rem,6vw,4.5rem);line-height:1.02;margin:0;letter-spacing:-.05em}header p{max-width:650px;color:var(--muted);margin:.9rem 0 30px}.toolbar{display:flex;align-items:center;gap:12px;margin:0 0 24px}.toolbar input,.toolbar select{border:1px solid var(--line);border-radius:10px;background:#111a2c;color:var(--text);font:inherit;padding:11px 13px}.toolbar input{flex:1;min-width:180px}.request-button{border:0;border-radius:10px;background:var(--accent);color:#07111d;font:700 .9rem system-ui;padding:11px 14px;cursor:pointer}.request-button:disabled{background:#44516a;color:#c1cada}.search-results{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px}.search-card{display:grid;grid-template-columns:116px 1fr;gap:18px;background:linear-gradient(145deg,var(--panel),#10182a);border:1px solid var(--line);border-radius:18px;padding:14px}.search-poster{width:116px;height:174px;border-radius:11px;object-fit:cover;background:#263653}.poster-fallback{display:grid;place-items:center;font-size:2.5rem;color:var(--accent)}.source{float:right;color:var(--muted);font-size:.72rem}.source-link{display:inline-block;color:var(--accent);margin-top:10px;text-decoration:none}.metadata,.creator{color:var(--muted);font-size:.85rem}.overview{color:#dce4f1}.empty{padding:50px;border:1px dashed var(--line);border-radius:18px;color:var(--muted)}footer{color:var(--muted);font-size:.8rem;margin-top:28px}@media(max-width:600px){main{padding:26px 14px 50px}.toolbar{display:grid}.search-card{grid-template-columns:92px 1fr}.search-poster{width:92px;height:138px}}
</style>
"""
    script = """
<script>
const input=document.querySelector('#provider-search'); const type=document.querySelector('#provider-type'); const button=document.querySelector('#provider-submit'); const results=document.querySelector('#provider-results');
function esc(v){const n=document.createElement('div');n.textContent=v||'';return n.innerHTML;}
async function run(){const q=input.value.trim();if(!q){results.hidden=true;results.innerHTML='';return;}button.disabled=true;button.textContent='Searching…';try{const r=await fetch('/api/search?q='+encodeURIComponent(q)+'&type='+encodeURIComponent(type.value));const data=await r.json();if(!r.ok)throw new Error(data.error||'Search failed');results.innerHTML=data.length?data.map(i=>{const p=i.poster_path?`<img class='search-poster' src='${esc(i.poster_path)}' alt='' loading='lazy'>`:`<div class='search-poster poster-fallback'>✦</div>`;const c=i.artist||i.author?`<div class='creator'>${esc(i.artist||i.author)}</div>`:'';const s=i.source_url?`<a class='source-link' href='${esc(i.source_url)}' target='_blank' rel='noopener noreferrer'>Open source ↗</a>`:'';return `<article class='search-card'>${p}<div><div class='eyebrow'>${esc(i.media_type)} <span class='source'>${esc(i.source_label)}</span></div><h2>${esc(i.title)}</h2><p class='metadata'>${esc(i.year||'')}</p>${c}<p class='overview'>${esc(i.overview||'No synopsis available.')}</p>${s}</div></article>`}).join(''):`<div class='empty'>No results found across the selected sources.</div>`;results.hidden=false;}catch(e){results.innerHTML=`<div class='empty'>${esc(e.message)}</div>`;results.hidden=false;}button.disabled=false;button.textContent='Search all media';}
button.addEventListener('click',run);input.addEventListener('keydown',e=>{if(e.key==='Enter')run();});
</script>
"""
    return "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><meta name='theme-color' content='#0b1020'><link rel='icon' href='/icon-32.png'><title>Media Search</title>" + style + "</head><body><main><nav class='page-nav' aria-label='Media portal pages'><a class='page-pill' href='/'>Recommendations</a><a class='page-pill active' href='/search'>Search</a></nav><header><div><div class='kicker'>Private media concierge</div><h1>Find something specific</h1><p>Search films, TV, books, audiobooks and music across the connected metadata providers. Search is read-only.</p></div></header><div class='toolbar'><input id='provider-search' type='search' placeholder='Title, author, artist or keyword…' autocomplete='off'><select id='provider-type' aria-label='Media type'><option value='all'>All media</option><option value='movie'>Films</option><option value='tv'>TV</option><option value='ebook'>Books</option><option value='audiobook'>Audiobooks</option><option value='album'>Music</option></select><button id='provider-submit' class='request-button' type='button'>Search all media</button></div><section id='provider-results' class='search-results' hidden aria-live='polite'></section><footer>Sources: TMDB via Seerr, Open Library and MusicBrainz. Use the Recommendations page for explicit requests.</footer></main>" + script + "</body></html>"


def action_key(item: Mapping[str, Any]) -> str:
    raw = "|".join(str(item.get(key, "")) for key in ("authority", "authority_id"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _read_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    with STATE_PATH.open(encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def _write_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)
    os.chmod(temporary, 0o600)
    os.replace(temporary, STATE_PATH)


def _request_json(url: str, *, method: str = "GET", body: Any = None,
                  headers: Optional[Mapping[str, str]] = None) -> tuple[int, Any, Mapping[str, str]]:
    encoded = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read()
            try:
                decoded = json.loads(payload or b"{}")
            except json.JSONDecodeError:
                decoded = payload.decode("utf-8", "replace")[:300]
            return response.status, decoded, dict(response.headers)
    except urllib.error.HTTPError as error:
        payload = error.read()
        try:
            decoded = json.loads(payload or b"{}")
        except json.JSONDecodeError:
            decoded = {"error": payload.decode("utf-8", "replace")[:300]}
        return error.code, decoded, dict(error.headers)


def _find_candidate(items: list[dict[str, Any]], body: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    matches = [item for item in items if item.get("authority") == body.get("authority")
               and str(item.get("authority_id")) == str(body.get("authority_id"))
               and item.get("title") == body.get("title")]
    return matches[0] if len(matches) == 1 else None


def _seerr_request(item: Mapping[str, Any]) -> dict[str, Any]:
    password_path = Path(os.environ["SEERR_PASSWORD_PATH"])
    password = password_path.read_text(encoding="utf-8").strip()
    login_body = {"email": os.environ["SEERR_EMAIL"], "password": password}
    status, _, headers = _request_json(os.environ["SEERR_URL"] + "/api/v1/auth/local",
                                       method="POST", body=login_body,
                                       headers={"Content-Type": "application/json"})
    if status != 200:
        raise RuntimeError("Seerr login failed")
    cookie = headers.get("Set-Cookie", "").split(";", 1)[0]
    if not cookie:
        raise RuntimeError("Seerr login returned no session cookie")
    body = {"mediaType": item["media_type"], "mediaId": int(item["authority_id"])}
    if item.get("media_type") == "tv":
        seasons = item.get("seasons")
        if not isinstance(seasons, list) or not seasons:
            raise RuntimeError("TV candidate has no validated seasons")
        body["seasons"] = seasons
    status, response, _ = _request_json(
        os.environ["SEERR_URL"] + "/api/v1/request", method="POST",
        body=body,
        headers={"Content-Type": "application/json", "Cookie": cookie},
    )
    if status not in (200, 201):
        raise RuntimeError("Seerr request was rejected")
    return {"authority": "seerr", "request_id": response.get("id"), "response": response}


def _lidarr_request(item: Mapping[str, Any]) -> dict[str, Any]:
    key = Path(os.environ["LIDARR_API_KEY_PATH"]).read_text(encoding="utf-8").strip()
    base = os.environ["LIDARR_URL"]
    headers = {"X-Api-Key": key}
    existing_query = urllib.parse.urlencode({"foreignAlbumId": item["authority_id"]})
    existing_status, existing, _ = _request_json(base + "/api/v1/album?" + existing_query, headers=headers)
    if existing_status != 200 or existing:
        raise RuntimeError("Lidarr candidate is no longer unowned")
    query = urllib.parse.urlencode({"term": item["title"]})
    status, lookup, _ = _request_json(base + "/api/v1/album/lookup?" + query, headers=headers)
    matches = [x for x in lookup if x.get("foreignAlbumId") == item["authority_id"]]
    if status != 200 or len(matches) != 1:
        raise RuntimeError("Lidarr candidate revalidation was ambiguous")
    body = dict(matches[0])
    body.update({"rootFolderPath": os.environ["LIDARR_ROOT"],
                 "qualityProfileId": int(os.environ["LIDARR_QUALITY_PROFILE_ID"]),
                 "metadataProfileId": int(os.environ["LIDARR_METADATA_PROFILE_ID"]),
                 "monitored": True,
                 "addOptions": {"monitor": "all", "searchForNewAlbum": True}})
    artist = dict(body.get("artist") or {})
    artist.update({"rootFolderPath": os.environ["LIDARR_ROOT"],
                   "qualityProfileId": int(os.environ["LIDARR_QUALITY_PROFILE_ID"]),
                   "metadataProfileId": int(os.environ["LIDARR_METADATA_PROFILE_ID"]),
                   # A one-album request must not start following the artist.
                   "monitored": False,
                   "monitorNewItems": "none",
                   "addOptions": {"monitor": "none", "searchForMissingAlbums": False}})
    body["artist"] = artist
    status, response, _ = _request_json(base + "/api/v1/album", method="POST", body=body,
                                        headers={"X-Api-Key": key, "Content-Type": "application/json"})
    if status not in (200, 201):
        raise RuntimeError("Lidarr request was rejected")
    return {"authority": "lidarr", "request_id": response.get("id"), "response": response}


def _lazylibrarian_request(item: Mapping[str, Any]) -> dict[str, Any]:
    """Revalidate and queue one ebook/audiobook through LazyLibrarian."""
    key = Path(os.environ["LAZYLIBRARIAN_API_KEY_PATH"]).read_text(encoding="utf-8").strip()
    base = os.environ["LAZYLIBRARIAN_URL"].rstrip("/") + "/api"
    query = {"apikey": key, "cmd": "getAllBooks", "json": "1"}
    status, existing, _ = _request_json(base + "?" + urllib.parse.urlencode(query))
    if status != 200:
        raise RuntimeError("LazyLibrarian revalidation failed")
    books = existing.get("books", []) if isinstance(existing, Mapping) else existing
    if not isinstance(books, list):
        raise RuntimeError("LazyLibrarian returned an invalid library response")
    matches = [book for book in books if isinstance(book, Mapping) and
               str(book.get("BookID", book.get("bookid", ""))) == str(item["authority_id"])]
    if len(matches) > 1:
        raise RuntimeError("LazyLibrarian candidate has duplicate records")
    if matches:
        book = matches[0]
        existing_title = book.get("BookName", book.get("bookname", ""))
        if str(existing_title).casefold() != str(item["title"]).casefold():
            raise RuntimeError("LazyLibrarian candidate identity changed")
        status_values = {str(book.get(key, "")) for key in
                         ("Status", "status", "AudioStatus", "audiostatus")}
        if status_values & {"Wanted", "Have"}:
            raise RuntimeError("LazyLibrarian candidate is already tracked")
    add_query = {"apikey": key, "cmd": "addBook", "id": str(item["authority_id"]),
                 "wait": "1", "source": "OpenLibrary"}
    add_status, added, _ = _request_json(base + "?" + urllib.parse.urlencode(add_query))
    if add_status != 200 or added is False:
        raise RuntimeError("LazyLibrarian addBook was rejected")
    queue_query = {"apikey": key, "cmd": "queueBook", "id": str(item["authority_id"]),
                   "type": "AudioBook" if item.get("media_type") == "audiobook" else "eBook"}
    queue_status, queued, _ = _request_json(base + "?" + urllib.parse.urlencode(queue_query))
    if queue_status != 200 or queued != "OK":
        raise RuntimeError("LazyLibrarian queueBook was rejected")
    return {"authority": "lazylibrarian", "request_id": str(item["authority_id"]),
            "response": {"add": added, "queue": queued}}


def _search_openlibrary(query: str, media_type: str) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"q": query, "limit": 8, "mode": "everything"})
    status, payload, _ = _request_json("https://openlibrary.org/search.json?" + params)
    if status != 200 or not isinstance(payload, Mapping):
        return []
    results = []
    for doc in payload.get("docs", [])[:8]:
        if not isinstance(doc, Mapping) or not doc.get("key") or not doc.get("title"):
            continue
        key = str(doc["key"])
        cover = doc.get("cover_i")
        authors = doc.get("author_name") or []
        sentence = doc.get("first_sentence")
        if isinstance(sentence, list):
            sentence = sentence[0] if sentence else ""
        results.append({
            "media_type": media_type, "authority": "openlibrary", "authority_id": key,
            "title": str(doc["title"]), "author": str(authors[0]) if authors else "",
            "year": str(doc.get("first_publish_year") or ""), "overview": str(sentence or ""),
            "poster_path": f"https://covers.openlibrary.org/b/id/{cover}-M.jpg" if cover else "",
            "source_label": "Open Library search",
            "source_url": "https://openlibrary.org" + urllib.parse.quote(key, safe="/"),
            "explanation": "Read-only Open Library search result.",
        })
    return results


def _search_musicbrainz(query: str) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"query": query, "fmt": "json", "limit": 8})
    status, payload, _ = _request_json(
        "https://musicbrainz.org/ws/2/release-group/?" + params,
        headers={"User-Agent": "UnifiedMediaRecommendations/1.0 (private homelab)"})
    if status != 200 or not isinstance(payload, Mapping):
        return []
    results = []
    for group in payload.get("release-groups", [])[:8]:
        if not isinstance(group, Mapping) or not group.get("id") or not group.get("title"):
            continue
        credits = group.get("artist-credit") or [{}]
        artist = credits[0].get("name", "") if isinstance(credits[0], Mapping) else ""
        group_id = str(group["id"])
        results.append({
            "media_type": "album", "authority": "musicbrainz", "authority_id": group_id,
            "title": str(group["title"]), "artist": str(artist),
            "year": str(group.get("first-release-date", ""))[:4],
            "poster_path": f"https://coverartarchive.org/release-group/{group_id}/front-250",
            "source_label": "MusicBrainz search",
            "source_url": f"https://musicbrainz.org/release-group/{urllib.parse.quote(group_id)}",
            "explanation": "Read-only MusicBrainz release-group search result.",
        })
    return results


def _search_seerr(query: str, media_type: str) -> list[dict[str, Any]]:
    try:
        password = Path(os.environ["SEERR_PASSWORD_PATH"]).read_text(encoding="utf-8").strip()
        status, _, headers = _request_json(
            os.environ["SEERR_URL"] + "/api/v1/auth/local", method="POST",
            body={"email": os.environ["SEERR_EMAIL"], "password": password},
            headers={"Content-Type": "application/json"})
        if status != 200:
            return []
        cookie = headers.get("Set-Cookie", "").split(";", 1)[0]
        params = urllib.parse.urlencode({"query": query, "page": 1})
        status, payload, _ = _request_json(
            os.environ["SEERR_URL"] + "/api/v1/search?" + params,
            headers={"Cookie": cookie})
    except (KeyError, OSError, ValueError, urllib.error.URLError):
        return []
    if status != 200 or not isinstance(payload, Mapping):
        return []
    results = []
    for item in payload.get("results", [])[:8]:
        if not isinstance(item, Mapping) or not item.get("id"):
            continue
        kind = str(item.get("mediaType") or item.get("media_type") or "")
        if kind not in {"movie", "tv"} or (media_type != "all" and kind != media_type):
            continue
        title = item.get("title") or item.get("name") or ""
        if not title:
            continue
        poster = str(item.get("posterPath") or item.get("poster_path") or "")
        results.append({
            "media_type": kind, "authority": "seerr", "authority_id": str(item["id"]),
            "title": str(title), "year": str(item.get("releaseDate") or item.get("firstAirDate") or "")[:4],
            "overview": str(item.get("overview") or ""),
            "poster_path": "https://image.tmdb.org/t/p/w500" + poster if poster.startswith("/") else poster,
            "source_label": "TMDB search via Seerr",
            "source_url": f"https://www.themoviedb.org/{kind}/{urllib.parse.quote(str(item['id']))}",
            "explanation": "Read-only TMDB search result through Seerr.",
        })
    return results


def search_all(query: str, media_type: str = "all") -> list[dict[str, Any]]:
    query = query.strip()
    media_type = media_type if media_type in {"all", "movie", "tv", "album", "ebook", "audiobook"} else "all"
    if not query or len(query) > 120:
        return []
    results = []
    if media_type in {"all", "movie", "tv"}:
        results.extend(_search_seerr(query, media_type))
    if media_type in {"all", "ebook", "audiobook"}:
        results.extend(_search_openlibrary(query, "ebook" if media_type == "all" else media_type))
    if media_type in {"all", "album"}:
        results.extend(_search_musicbrainz(query))
    return results[:24]


def submit_action(body: Mapping[str, Any]) -> dict[str, Any]:
    if not ACTION_ENABLED:
        raise RuntimeError("portal actions are disabled")
    if body.get("approve") is not True:
        raise RuntimeError("explicit approval is required")
    items = load_recommendations()
    item = _find_candidate(items, body)
    if item is None or item.get("owned") or item.get("archived") or item.get("match_count", 1) != 1:
        raise RuntimeError("candidate failed snapshot safety checks")
    key = action_key(item)
    state = _read_state()
    if key in state:
        return state[key]
    if item.get("authority") == "seerr":
        result = _seerr_request(item)
    elif item.get("authority") in {"lidarr", "musicbrainz"}:
        result = _lidarr_request(item)
    elif item.get("authority") in {"lazylibrarian", "openlibrary"}:
        result = _lazylibrarian_request(item)
    else:
        raise RuntimeError("unsupported write authority")
    state[key] = result
    _write_state(state)
    return result


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/health":
            self._send(200, b"ok", "text/plain; charset=utf-8")
            return
        if path == "/oauth/trakt/start":
            try:
                self.send_response(302)
                self.send_header("Location", _trakt_connect_url())
                self.end_headers()
            except (OSError, RuntimeError, ValueError) as exc:
                self._send(503, json.dumps({"error": str(exc)}).encode(), "application/json")
            return
        if path == "/oauth/trakt/callback":
            try:
                message = _trakt_callback(urllib.parse.parse_qs(parsed.query))
                self._send(200, message.encode(), "text/plain; charset=utf-8")
            except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
                self._send(400, json.dumps({"error": str(exc)}).encode(), "application/json")
            return
        if path == "/oauth/trakt/device":
            try:
                if TRAKT_DEVICE_STATE_PATH.exists():
                    device = json.loads(TRAKT_DEVICE_STATE_PATH.read_text(encoding="utf-8"))
                else:
                    device = _trakt_device_start()
                verification_url = html.escape(str(device.get("verification_url", "https://trakt.tv/activate")), quote=True)
                user_code = html.escape(str(device.get("user_code", "")))
                body = ("<!doctype html><html><body style='font:20px system-ui;padding:2rem'>"
                        "<h1>Connect Trakt</h1><p>Open <a href='" + verification_url + "' target='_blank' rel='noopener'>Trakt activation</a> in your normal browser.</p>"
                        "<p>Enter this code:</p><p style='font-size:3rem;letter-spacing:.2em'><strong>" + user_code + "</strong></p>"
                        "<p id='status'>Waiting for approval…</p><script>setInterval(async()=>{const r=await fetch('/oauth/trakt/device/status');const j=await r.json();document.querySelector('#status').textContent=j.status==='connected'?'Trakt connected. You may close this tab.':('Status: '+j.status)},5000)</script></body></html>")
                self._send(200, body.encode(), "text/html; charset=utf-8")
            except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
                self._send(503, json.dumps({"error": str(exc)}).encode(), "application/json")
            return
        if path == "/oauth/trakt/device/status":
            try:
                self._send(200, json.dumps({"status": _trakt_device_status()}).encode(), "application/json")
            except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
                self._send(400, json.dumps({"error": str(exc)}).encode(), "application/json")
            return
        if path == "/api/search":
            params = urllib.parse.parse_qs(parsed.query)
            query = (params.get("q") or [""])[0]
            media_type = (params.get("type") or ["all"])[0]
            try:
                self._send(200, json.dumps(search_all(query, media_type)).encode(), "application/json")
            except (OSError, ValueError, urllib.error.URLError) as exc:
                self._send(502, json.dumps({"error": str(exc)}).encode(), "application/json")
            return
        asset = STATIC_ASSETS.get(path)
        if asset:
            asset_path = ASSET_DIR / asset[0]
            try:
                payload = asset_path.read_bytes()
            except OSError:
                self._send(404, b"not found", "text/plain; charset=utf-8")
                return
            self._send(200, payload, asset[1], cache_control="public, max-age=86400")
            return
        if path == "/search":
            self._send(200, render_search_html().encode(), "text/html; charset=utf-8")
            return
        try:
            items = load_recommendations()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._send(503, json.dumps({"error": str(exc)}).encode(), "application/json")
            return
        if path == "/api/recommendations":
            self._send(200, json.dumps(items).encode(), "application/json")
        elif path == "/":
            self._send(200, render_html(items).encode(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/request":
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            result = submit_action(body)
            self._send(200, json.dumps(result).encode(), "application/json")
        except (KeyError, RuntimeError, ValueError, json.JSONDecodeError, OSError) as exc:
            self._send(409, json.dumps({"error": str(exc)}).encode(), "application/json")

    def _send(self, status: int, body: bytes, content_type: str,
              cache_control: Optional[str] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if cache_control:
            self.send_header("Cache-Control", cache_control)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_: object) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8787"))), Handler)
    server.serve_forever()
