#!/opt/news-aggregator/venv/bin/python3
"""Twice-daily digest layer: an abridged multi-source summary plus
deviation notes (what one outlet says that others don't) for each
recently-active MULTI-OUTLET cluster only. Runs on its own 06:00/18:00
timer, separate from the hourly breaking-news pipeline, and writes only to
digest_entries -- it never touches cluster_summaries, so it cannot affect
the breaking-news view. Same direct aster-llama client-call pattern as
summarize.py; does not touch Aster's own bounded function allowlist.

Deliberately excludes single-outlet clusters: a digest is meant to be a
curated set of notable, cross-verified stories, not a re-abridged copy of
every single RSS item that came through (those already display fine via
their own feed description in the breaking-news view). An early version
of this script digested every cluster regardless of outlet count and hit
546 entries in one day, only 21 of which were actually multi-outlet --
the other 525 were noise, not a digest.

Only regenerates a cluster's digest entry if it has no entry yet, or has
gained new items since its last one -- an unconditional re-scan of every
cluster inside the lookback window would re-run an expensive LLM call for
unchanged stories on every single run, which is exactly the bug an even
earlier version of this script had."""

from __future__ import annotations

import json
import sqlite3
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from digest_text import coherent_event, dedupe_titles, repeat_story

DB_PATH = Path(__file__).parent / "news.db"
ASTER_LLAMA_URL = "http://192.168.70.12:11435/v1/chat/completions"
MODEL = "qwen3.5-9b"
API_KEY_PATH = Path("/root/.news-aggregator-llama-key")

# Digest runs every 12h; a generous 14h lookback tolerates a missed/delayed
# run without dropping a story, matching cluster.py's own bounded-lookback
# precedent rather than an unbounded historical scan.
LOOKBACK = timedelta(hours=14)
MAX_STORIES = 21
WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"

ABRIDGED_SYSTEM_PROMPT = (
    "You write a longer, neutral, multi-source digest summary of a news "
    "story for a private reading app. You are given each outlet's headline "
    "and its own short description. Write 4-6 sentences covering what "
    "happened in more depth than a one-line summary would. Stay factual and "
    "neutral. Do not rate, label, or comment on any outlet's political bias "
    "or slant -- that is handled separately. Do not editorialize beyond "
    "what the sources themselves report."
)

DEVIATION_SYSTEM_PROMPT = (
    "You compare how different news outlets are covering the same event. "
    "You are given each outlet's headline and its own short description, "
    "labeled by outlet. Identify specific facts, claims, or angles that "
    "appear in only ONE outlet's coverage and not the others' -- a genuine "
    "difference, not a paraphrase of the same fact. Name the outlet and the "
    "specific thing it mentions that the others don't. If you don't find a "
    "real, checkable difference, say plainly that the outlets covered the "
    "story consistently -- do not invent a difference to have something to "
    "report. Keep it to 1-3 sentences."
)

IMAGE_QUERY_SYSTEM_PROMPT = (
    "Create a concise, neutral visual search query for an illustrative news "
    "image. Use 3-6 concrete topic or scene terms from the coverage. Avoid "
    "names, numbers, accusations, predictions, and time-sensitive claims; "
    "the image must not imply proof of a specific allegation. Return only "
    "the search query, with no punctuation or explanation."
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_source_lines(items: list[sqlite3.Row]) -> str:
    lines = []
    for item in items:
        lines.append(f"- [{item['feed_id']}] {item['title']}: {(item['summary'] or '')[:300]}")
    return "\n".join(lines)


def call_aster_llama(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }).encode()
    api_key = API_KEY_PATH.read_text().strip()
    request = urllib.request.Request(
        ASTER_LLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.load(response)
    return result["choices"][0]["message"]["content"].strip()


def pick_image(items: list[sqlite3.Row]) -> dict[str, str] | None:
    for item in items:
        if item["image_url"]:
            return {
                "url": item["image_url"],
                "credit": f"Story image · {item['feed_id']}",
                "source_url": item["link"] if "link" in item.keys() and item["link"] else "",
            }
    return None


def build_image_query(items: list[sqlite3.Row]) -> str:
    """Turn the existing story context into a conservative visual query."""
    source_lines = build_source_lines(items)
    try:
        query = call_aster_llama(
            IMAGE_QUERY_SYSTEM_PROMPT,
            f"Coverage of the same event:\n{source_lines}",
            max_tokens=48,
        )
    except Exception as exc:  # noqa: BLE001 - deterministic fallback keeps digest generation moving
        print(f"image query FAILED - {exc}")
        query = items[0]["title"] or "news event"
    query = " ".join(query.replace("\n", " ").split())
    return query[:180] or "news event"


def find_commons_image(query: str) -> dict[str, str] | None:
    """Find a landscape-friendly open image for a story with no source image.

    Wikimedia search also returns reports and other documents, so only image
    MIME types with usable thumbnails are accepted. The result is cached in
    digest_entries; the reader-facing app never performs this search.
    """
    query_variants = [query]
    lowered = query.lower()
    category_queries = (
        (("school", "secondary school", "evacuation", "student"), "secondary school building Canada"),
        (("winery", "vineyard", "wine", "events centre"), "vineyard winery building"),
        (("podcast", "broadcast", "radio"), "podcast recording studio microphone"),
        (("court", "guilty", "manslaughter", "sentence", "trial"), "courthouse exterior Canada"),
        (("acquire", "acquires", "economic development", "business"), "local business building Canada"),
    )
    for terms, broad_query in category_queries:
        if any(term in lowered for term in terms):
            query_variants.append(broad_query)
            break

    for search_query in query_variants:
        params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": search_query,
        "gsrnamespace": "6",
        "gsrlimit": "8",
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": "1200",
        "format": "json",
        "origin": "*",
        }
        url = WIKIMEDIA_API_URL + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={"User-Agent": "AsterNewsBriefing/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = json.load(response)
        except Exception as exc:  # noqa: BLE001 - an optional image must not lose a story
            print(f"commons image lookup FAILED for {search_query!r} - {exc}")
            continue

        for page in payload.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [{}])[0]
            mime = (info.get("mime") or "").lower()
            thumb_url = info.get("thumburl") or info.get("url")
            source_url = info.get("descriptionurl")
            if mime not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
                continue
            if not thumb_url or not source_url:
                continue
            title = page.get("title", "").removeprefix("File:")
            return {
                "url": thumb_url,
                "credit": f"Illustrative image · Wikimedia Commons · {title}",
                "source_url": source_url,
            }
    return None


def ensure_digest_image_columns(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(digest_entries)")}
    if "image_credit" not in columns:
        conn.execute("ALTER TABLE digest_entries ADD COLUMN image_credit TEXT")
    if "image_source_url" not in columns:
        conn.execute("ALTER TABLE digest_entries ADD COLUMN image_source_url TEXT")
    conn.commit()


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_digest_image_columns(conn)

    cutoff = (datetime.now(timezone.utc) - LOOKBACK).isoformat()
    cluster_rows = conn.execute(
        "SELECT fi.cluster_id, MAX(fi.fetched_at) AS latest, MIN(fi.title) AS title, "
        "GROUP_CONCAT(COALESCE(fi.title, '') || ' ' || COALESCE(fi.summary, ''), ' ') AS text "
        "FROM feed_items fi "
        "LEFT JOIN digest_entries de ON de.cluster_id = fi.cluster_id "
        "WHERE fi.cluster_id IS NOT NULL AND fi.fetched_at >= ? "
        "AND (de.cluster_id IS NULL OR fi.fetched_at > de.generated_at) "
        "AND fi.cluster_id IN ("
        "    SELECT cluster_id FROM feed_items"
        "    GROUP BY cluster_id HAVING COUNT(DISTINCT feed_id) > 1"
        ") GROUP BY fi.cluster_id ORDER BY latest DESC",
        (cutoff,),
    ).fetchall()
    previous_run = conn.execute("SELECT MAX(digest_run) FROM digest_entries").fetchone()[0]
    previous_titles = []
    if previous_run:
        previous_titles = [
            row["title"] for row in conn.execute(
                "SELECT fi.title FROM feed_items fi "
                "JOIN (SELECT DISTINCT cluster_id FROM digest_entries WHERE digest_run = ?) old "
                "ON old.cluster_id = fi.cluster_id",
                (previous_run,),
            ).fetchall()
        ]
    clusters = [
        row["cluster_id"] for row in dedupe_titles(cluster_rows, text_key="text")
        if not any(repeat_story(row["title"], old_title) for old_title in previous_titles)
    ][:MAX_STORIES]

    digest_run = now_iso()
    print(f"{len(clusters)} clusters active in the last {LOOKBACK} to digest")

    for cluster_id in clusters:
        items = conn.execute(
            "SELECT feed_id, title, summary, image_url, link FROM feed_items WHERE cluster_id = ?",
            (cluster_id,),
        ).fetchall()
        items = coherent_event(items)
        if not items:
            continue
        outlet_count = len({item["feed_id"] for item in items})
        if outlet_count < 2:
            continue
        source_lines = build_source_lines(items)

        try:
            abridged = call_aster_llama(
                ABRIDGED_SYSTEM_PROMPT,
                f"Outlet coverage of the same event:\n{source_lines}",
                max_tokens=350,
            )
        except Exception as exc:  # noqa: BLE001 - log and continue with remaining clusters
            print(f"cluster {cluster_id}: abridged summary FAILED - {exc}")
            continue

        deviation = None
        if outlet_count > 1:
            try:
                deviation = call_aster_llama(
                    DEVIATION_SYSTEM_PROMPT,
                    f"Outlet coverage of the same event, by outlet:\n{source_lines}",
                    max_tokens=150,
                )
            except Exception as exc:  # noqa: BLE001 - the abridged summary still stands alone
                print(f"cluster {cluster_id}: deviation notes FAILED - {exc}")

        image = pick_image(items)
        if image is None:
            fallback = find_commons_image(build_image_query(items))
            if fallback:
                image = fallback

        conn.execute(
            "INSERT OR REPLACE INTO digest_entries "
            "(cluster_id, abridged_summary, deviation_notes, image_url, image_credit, image_source_url, digest_run, generated_at, model) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cluster_id, abridged, deviation, image["url"] if image else None,
             image["credit"] if image else None, image["source_url"] if image else None,
             digest_run, now_iso(), MODEL),
        )
        conn.commit()
        print(f"cluster {cluster_id} ({outlet_count} outlets): digested" + (" with deviation notes" if deviation else ""))

    conn.close()


if __name__ == "__main__":
    main()
