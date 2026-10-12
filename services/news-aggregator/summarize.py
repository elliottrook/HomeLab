#!/opt/news-aggregator/venv/bin/python3
"""Summarize multi-outlet clusters via the shared aster-llama endpoint."""

import json
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "news.db"
ASTER_LLAMA_URL = "http://192.168.70.12:11435/v1/chat/completions"
MODEL = "qwen3.5-9b"
API_KEY_PATH = Path("/root/.news-aggregator-llama-key")

SYSTEM_PROMPT = (
    "You summarize how multiple news outlets are covering the same event. "
    "You are given each outlet's headline and its own short description. "
    "Write a neutral, factual 2-3 sentence summary of what happened. "
    "If the outlets notably differ in what they emphasize or report, say so "
    "briefly in one additional sentence. Do not rate, label, or comment on "
    "any outlet's political bias or slant -- that is handled separately. "
    "Do not editorialize beyond what the sources themselves report."
)


def build_user_prompt(items: list[sqlite3.Row]) -> str:
    lines = ["Outlet coverage of the same event:"]
    for item in items:
        lines.append(f"- [{item['feed_id']}] {item['title']}: {item['summary'][:300]}")
    return "\n".join(lines)


def call_aster_llama(cluster_items: list[sqlite3.Row]) -> str:
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(cluster_items)},
        ],
        "temperature": 0.2,
        "max_tokens": 200,
    }).encode()
    api_key = API_KEY_PATH.read_text().strip()
    request = urllib.request.Request(
        ASTER_LLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)
    return result["choices"][0]["message"]["content"].strip()


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pending = conn.execute(
        "SELECT cluster_id, COUNT(DISTINCT feed_id) AS outlet_count "
        "FROM feed_items WHERE cluster_id IS NOT NULL "
        "AND cluster_id NOT IN (SELECT cluster_id FROM cluster_summaries) "
        "GROUP BY cluster_id HAVING outlet_count > 1"
    ).fetchall()
    print(f"{len(pending)} multi-outlet clusters need summaries")
    for row in pending:
        cluster_id = row["cluster_id"]
        items = conn.execute(
            "SELECT feed_id, title, summary FROM feed_items WHERE cluster_id = ?",
            (cluster_id,),
        ).fetchall()
        try:
            summary = call_aster_llama(items)
        except Exception as exc:  # noqa: BLE001
            print(f"cluster {cluster_id}: FAILED - {exc}")
            continue
        conn.execute(
            "INSERT INTO cluster_summaries (cluster_id, summary, outlet_count, generated_at, model) "
            "VALUES (?, ?, ?, ?, ?)",
            (cluster_id, summary, row["outlet_count"], datetime.now(timezone.utc).isoformat(), MODEL),
        )
        conn.commit()
        print(f"cluster {cluster_id} ({row['outlet_count']} outlets): {summary[:80]}...")
    conn.close()


if __name__ == "__main__":
    main()
