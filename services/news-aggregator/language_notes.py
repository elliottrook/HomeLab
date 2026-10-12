#!/opt/news-aggregator/venv/bin/python3
"""Optionally flag notably loaded language in individual stories."""

import json
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "news.db"
ASTER_LLAMA_URL = "http://192.168.70.12:11435/v1/chat/completions"
MODEL = "qwen3.5-9b"
API_KEY_PATH = Path("/root/.news-aggregator-llama-key")
BATCH_LIMIT = 50

SYSTEM_PROMPT = (
    "You review a single news headline and its short description for notably "
    "loaded, emotionally charged, or one-sided language -- not for factual "
    "accuracy, and not to rate the outlet's overall politics. Most headlines "
    "are ordinary and deserve no comment. Reply with exactly the word NONE if "
    "nothing stands out. Only if something genuinely notable is present, reply "
    "with one short, specific sentence naming the loaded word or phrase."
)


def check_one(title: str, summary: str, api_key: str) -> str | None:
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Headline: {title}\nDescription: {(summary or '')[:300]}"},
        ],
        "temperature": 0.1,
        "max_tokens": 80,
    }).encode()
    request = urllib.request.Request(
        ASTER_LLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)
    text = result["choices"][0]["message"]["content"].strip()
    return None if text.upper().startswith("NONE") else text


def main() -> None:
    api_key = API_KEY_PATH.read_text().strip()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pending = conn.execute(
        "SELECT id, title, summary FROM feed_items "
        "WHERE id NOT IN (SELECT item_id FROM item_language_notes) "
        "ORDER BY id DESC LIMIT ?", (BATCH_LIMIT,),
    ).fetchall()
    print(f"checking {len(pending)} items (batch limit {BATCH_LIMIT})")
    flagged = 0
    for item in pending:
        try:
            note = check_one(item["title"], item["summary"], api_key)
        except Exception as exc:  # noqa: BLE001
            print(f"item {item['id']}: FAILED - {exc}")
            continue
        conn.execute(
            "INSERT INTO item_language_notes (item_id, note, generated_at, model) VALUES (?, ?, ?, ?)",
            (item["id"], note, datetime.now(timezone.utc).isoformat(), MODEL),
        )
        conn.commit()
        if note:
            flagged += 1
            print(f"item {item['id']}: {note}")
    print(f"{flagged}/{len(pending)} items flagged")
    conn.close()


if __name__ == "__main__":
    main()
