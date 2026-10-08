#!/opt/news-aggregator/venv/bin/python3
"""Phase 3: narrate the latest digest run as a single audio briefing.

Runs right after digest.py in the same 05:15/17:15 timer, not on its own
schedule -- there is nothing to narrate until a digest run has happened.
Only narrates the entries from the most recent digest_run (a "morning/
evening briefing" of what's new since last time), not the full rolling
/digest page history. Deviation notes are deliberately skipped -- they
read fine on a page but don't flow naturally when spoken; headline plus
abridged summary is the whole script for v1.

Kokoro (local, offline) does the synthesis; ffmpeg transcodes its
WAV output to MP3 for a much smaller file over a phone/cellular
connection. Overwrites one fixed file each run rather than accumulating a
history, matching digest_entries' own replace-not-append design.

The intro/outro and each story are synthesized as separate Piper calls and
concatenated with a fixed silence gap between stories, rather than one
single Piper call over the whole script -- Piper's own sentence/newline
pausing wasn't enough separation between stories once heard for real."""

import argparse
import json
import re
import subprocess
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from digest_text import coherent_event, dedupe_titles, repeat_story, speech_text

DB_PATH = Path(__file__).parent / "news.db"
STATIC_DIR = Path(__file__).parent / "static" / "digest-audio"
VOICE_MODEL = Path("/opt/news-aggregator/models/kokoro/kokoro-v1.0.fp16.onnx")
VOICE_PACK = Path("/opt/news-aggregator/models/kokoro/voices-v1.0.bin")
VOICE = "bm_daniel"
VOICE_SPEED = 0.95
STORY_PAUSE_SECONDS = 1.0
MAX_STORIES = 21

# BC no longer observes DST; matches app.py's own get_audio_meta() convention
BC_OFFSET = timedelta(hours=-7)

WAV_PATH = STATIC_DIR / "latest.wav"
MP3_PATH = STATIC_DIR / "latest.mp3"
META_PATH = STATIC_DIR / "latest.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def local_now() -> datetime:
    return datetime.now(timezone.utc) + BC_OFFSET


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def briefing_label(local_dt: datetime) -> tuple[str, str]:
    period = "morning" if local_dt.hour < 12 else "evening"
    date_str = local_dt.strftime("%A, %B ") + ordinal(local_dt.day)
    return period, date_str


def synth(text: str, out_path: Path, engine: Kokoro) -> None:
    # Keep long summaries from crossing Kokoro's internal phoneme-window
    # boundary.  Sentence/clause-sized calls preserve pauses while avoiding
    # the rough prosody and breathy joins that can appear in long batches.
    chunks = []
    for sentence in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ").strip()):
        sentence = sentence.strip()
        if not sentence:
            continue
        clause_pattern = r"(?<=[;:])\s+|(?<=,)\s+(?=[A-ZÀ-ÖØ-Þ])"
        if len(sentence) > 240:
            clause_pattern = r"(?<=[;:,])\s+"
        clauses = re.split(clause_pattern, sentence)
        chunks.extend(clause.strip() for clause in clauses if clause.strip())

    rendered = []
    sample_rate = None
    for chunk in chunks:
        audio, sample_rate = engine.create(
            chunk, voice=VOICE, speed=VOICE_SPEED, lang="en-gb"
        )
        rendered.append(audio)
    if not rendered or sample_rate is None:
        raise ValueError("No speech chunks generated")
    audio = np.concatenate(rendered)
    sf.write(out_path, audio, sample_rate, subtype="PCM_16")


def silence_clip(out_path: Path, seconds: float) -> None:
    result = subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
         "-t", str(seconds), "-c:a", "pcm_s16le", str(out_path)],
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg silence generation FAILED: {result.stderr.decode(errors='replace')}")


def concat_wavs(clip_paths: list, out_path: Path) -> None:
    list_file = out_path.with_suffix(".txt")
    list_file.write_text("".join(f"file '{p}'\n" for p in clip_paths))
    result = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out_path)],
        capture_output=True,
        timeout=60,
    )
    list_file.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg concat FAILED: {result.stderr.decode(errors='replace')}")


def build_briefing(entries: list, engine: Kokoro, workdir: Path) -> tuple[Path, list[dict]]:
    period, date_str = briefing_label(local_now())
    intro_text = f"This is your {period} briefing for {date_str}."
    outro_text = f"That was your daily briefing for {date_str}."

    pause_wav = workdir / "pause.wav"
    silence_clip(pause_wav, STORY_PAUSE_SECONDS)

    clips = []
    chapters = []
    intro_wav = workdir / "00-intro.wav"
    synth(intro_text, intro_wav, engine)
    clips.append(intro_wav)
    elapsed = sf.info(intro_wav).duration

    for i, e in enumerate(entries):
        clips.append(pause_wav)
        elapsed += STORY_PAUSE_SECONDS
        story_wav = workdir / f"story-{i:02d}.wav"
        story_text = speech_text(e["headline"] + ".\n" + e["abridged_summary"])
        synth(story_text, story_wav, engine)
        chapters.append({"index": i + 1, "title": e["headline"], "start": round(elapsed, 3)})
        elapsed += sf.info(story_wav).duration
        clips.append(story_wav)

    clips.append(pause_wav)
    outro_wav = workdir / "99-outro.wav"
    synth(outro_text, outro_wav, engine)
    clips.append(outro_wav)

    combined = workdir / "combined.wav"
    concat_wavs(clips, combined)
    return combined, chapters


def vtt_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remainder = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remainder:06.3f}"


def write_chapters_vtt(path: Path, chapters: list[dict], duration: float) -> None:
    lines = ["WEBVTT", ""]
    for position, chapter in enumerate(chapters):
        end = chapters[position + 1]["start"] if position + 1 < len(chapters) else duration
        lines.extend([
            str(chapter["index"]),
            f"{vtt_timestamp(chapter['start'])} --> {vtt_timestamp(end)}",
            chapter["title"],
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def transcode_mp3(wav_path: Path, mp3_path: Path) -> None:
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-qscale:a", "4", str(mp3_path)],
        capture_output=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg mp3 transcode FAILED: {result.stderr.decode(errors='replace')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice-model", type=Path, default=VOICE_MODEL,
                         help="override voice model path (for A/B testing without touching production)")
    parser.add_argument("--out-dir", type=Path, default=STATIC_DIR,
                         help="override output directory (for A/B testing without touching production)")
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    mp3_path = out_dir / "latest.mp3"
    meta_path = out_dir / "latest.json"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    latest_run = conn.execute("SELECT MAX(digest_run) AS r FROM digest_entries").fetchone()["r"]
    if not latest_run:
        print("no digest_entries yet -- nothing to narrate")
        return 0

    entries = conn.execute(
        "SELECT de.cluster_id, de.abridged_summary, "
        "  (SELECT title FROM feed_items WHERE feed_items.cluster_id = de.cluster_id LIMIT 1) AS headline "
        "FROM digest_entries de WHERE de.digest_run = ? ORDER BY de.generated_at",
        (latest_run,),
    ).fetchall()
    previous_run = conn.execute(
        "SELECT MAX(digest_run) FROM digest_entries WHERE digest_run < ?",
        (latest_run,),
    ).fetchone()[0]
    if previous_run:
        previous_entries = conn.execute(
            "SELECT abridged_summary, "
            "(SELECT title FROM feed_items WHERE feed_items.cluster_id = de.cluster_id LIMIT 1) AS headline "
            "FROM digest_entries de WHERE digest_run = ?",
            (previous_run,),
        ).fetchall()
        entries = [entry for entry in entries if not any(
            repeat_story(entry["headline"], old["headline"]) for old in previous_entries
        )]
    coherent_entries = []
    for entry in entries:
        items = conn.execute(
            "SELECT feed_id, title FROM feed_items WHERE cluster_id = ?",
            (entry["cluster_id"],),
        ).fetchall()
        items = coherent_event(items)
        if len({item["feed_id"] for item in items}) >= 2:
            coherent_entries.append(entry)
    entries = coherent_entries
    entries = dedupe_titles(entries, "headline", "abridged_summary")
    entries = entries[:MAX_STORIES]
    conn.close()

    if not entries:
        print(f"digest_run {latest_run} has no entries -- nothing to narrate")
        return 0

    with tempfile.TemporaryDirectory(prefix="audio-digest-") as tmp:
        engine = Kokoro(str(args.voice_model), str(VOICE_PACK))
        try:
            combined_wav, chapters = build_briefing(entries, engine, Path(tmp))
        finally:
            engine.voices.close()
        transcode_mp3(combined_wav, mp3_path)
        write_chapters_vtt(out_dir / "latest.vtt", chapters, sf.info(combined_wav).duration)

    meta_path.write_text(json.dumps({
        "digest_run": latest_run,
        "generated_at": now_iso(),
        "story_count": len(entries),
        "chapters": chapters,
    }))

    print(f"audio digest generated: {len(entries)} stories, {mp3_path.stat().st_size} bytes -> {mp3_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
