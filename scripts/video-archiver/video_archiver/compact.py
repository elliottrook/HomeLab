"""Archive compaction: re-encode oversized files already in the archive roots.

Jason (2026-09-24): "identify files larger than 2.5 GB ... create a process to transcode
all large files down ... maintain the highest resolution possible - 1080p is preferred."

Design (see docs/projects/Archive-Large-File-Compaction.md):
- Candidates: video files in movies_archive_root / tv_archive_root larger than
  size_threshold_bytes, in a container that can hold HEVC under the SAME path
  (.mkv, .mp4, .m4v). The output replaces the source at the identical path, so
  Jellyfin keeps the same item (collections, watch state, metadata).
- Resolution: never upscale; cap at 1920x1080 with the aspect ratio preserved (computed
  here, not by scale_vaapi min() per axis, which distorts scope/widescreen sources).
- Size: aim for the archiver's target_size_bytes; if that would push 1080p below its
  quality floor, allow the file to grow toward cap_bytes before stepping down to 720p.
  Per-resolution bitrate ceilings stop short content wasting bits.
- HDR10/HLG sources (including Dolby Vision profile 7/8 base layers) stay HDR:
  10-bit HEVC main10 with BT.2020/PQ-or-HLG signalling. DV profile 5 has no HDR10
  base layer and is skipped. Non-HEVC-capable containers are reported, not converted.
- Audio and subtitles reuse the archiver's policy: one audio track (default, else
  English, else first); English subtitles only.
- Nothing replaces a source until the output passes verification: size (below both
  cap_bytes and max_output_fraction of the source), duration, codec/resolution, and a
  three-point decode spot-check. The source must be unchanged since it was probed.
- Before the first replacement of a run, a ZFS snapshot of the dataset is taken
  (rollback window); snapshots older than snapshot_retention_days are destroyed.
- One file at a time, sharing the archiver's lock; stops starting new files after the
  deadline. Every decision goes to a JSON-lines log and a persistent state file.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import Config
from .pipeline import LockHeldError, RunLogger, run_lock
from .transcode import (HIGH_BITRATE_AUDIO_CODECS, HIGH_BITRATE_THRESHOLD_BPS,
                        FALLBACK_AUDIO_KBPS_IF_UNKNOWN, _select_primary_audio_stream,
                        AudioStreamInfo)

log = logging.getLogger("video_archiver.compact")

DEFAULTS = dict(
    size_threshold_bytes=2_500_000_000,
    cap_bytes=2_300_000_000,
    max_output_fraction=0.80,
    snapshot_dataset="Media/data",
    snapshot_retention_days=7,
    deadline="07:00",
)
SAME_PATH_CONTAINERS = {".mkv": "matroska", ".mp4": "mp4", ".m4v": "mp4"}
MP4_AUDIO_COPY_OK = {"aac", "ac3", "eac3", "mp3", "alac"}
# (tier, max_w, max_h, floor_kbps, aim_sdr, aim_hdr, ceiling_sdr, ceiling_hdr)
# floor: below this the tier is not funded and we step down a resolution.
# aim:   preferred minimum when the size cap allows it (hardware HEVC needs more bits
#        than software x265 for the same quality).
TIERS = [
    ("1080p", 1920, 1080, 1200, 2000, 2500, 5000, 6000),
    ("720p", 1280, 720, 700, 1200, 1500, 2000, 2500),
    ("SD", 1024, 576, 400, 700, 700, 1200, 1200),
]
VIDEO_EXTS = {".mkv", ".mp4", ".m4v", ".avi", ".ts", ".m2ts", ".mpg", ".mov", ".wmv"}


class SkipFile(RuntimeError):
    pass


@dataclass
class SrcInfo:
    duration_s: float
    width: int
    height: int
    vcodec: str
    transfer: str | None
    dv_profile: int | None
    audio: list
    subs: list  # (input index, language, codec)


@dataclass
class Plan:
    tier: str
    out_w: int
    out_h: int
    video_kbps: int
    hdr: str | None  # None | "pq" | "hlg"
    audio_index: int
    audio_args: list
    audio_kbps: int
    sub_indices: list
    muxer: str
    predicted_bytes: int


def _run(cmd, timeout=None):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def probe_full(path: Path, cfg: Config) -> SrcInfo:
    r = _run([cfg.ffprobe_bin, "-v", "error", "-print_format", "json", "-show_format",
              "-show_streams", str(path)], timeout=300)
    if r.returncode != 0:
        raise SkipFile(f"ffprobe failed: {r.stderr[:300]}")
    d = json.loads(r.stdout)
    dur = float(d.get("format", {}).get("duration") or 0)
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"
              and not s.get("disposition", {}).get("attached_pic")), None)
    if not v or not dur:
        raise SkipFile("no usable video stream or duration")
    dv = None
    for sd in v.get("side_data_list") or []:
        if "dv_profile" in sd:
            dv = int(sd["dv_profile"])
    audio, subs = [], []
    ai = si = 0
    for s in d.get("streams", []):
        if s.get("codec_type") == "audio":
            br = s.get("bit_rate")
            audio.append(AudioStreamInfo(index=ai, codec_name=s.get("codec_name", ""),
                                         channels=int(s.get("channels", 2)),
                                         bit_rate=int(br) if br else None,
                                         is_default=bool(s.get("disposition", {}).get("default")),
                                         language=(s.get("tags") or {}).get("language")))
            ai += 1
        elif s.get("codec_type") == "subtitle":
            subs.append((si, (s.get("tags") or {}).get("language"), s.get("codec_name")))
            si += 1
    return SrcInfo(duration_s=dur, width=int(v.get("width", 0)), height=int(v.get("height", 0)),
                   vcodec=v.get("codec_name", ""), transfer=v.get("color_transfer"),
                   dv_profile=dv, audio=audio, subs=subs)


def _fit(w: int, h: int, max_w: int, max_h: int) -> tuple[int, int]:
    s = min(1.0, max_w / w, max_h / h)
    ow, oh = int(round(w * s / 2)) * 2, int(round(h * s / 2)) * 2
    return max(ow, 2), max(oh, 2)


def make_plan(src: Path, info: SrcInfo, cfg: Config, opts: dict) -> Plan:
    ext = src.suffix.lower()
    muxer = SAME_PATH_CONTAINERS.get(ext)
    if not muxer:
        raise SkipFile(f"container {ext} cannot hold HEVC under the same path; convert manually")
    if info.dv_profile == 5:
        raise SkipFile("Dolby Vision profile 5 has no HDR10 base layer; re-encoding would corrupt colour")
    if not info.audio:
        raise SkipFile("no audio stream")

    hdr = {"smpte2084": "pq", "arib-std-b67": "hlg"}.get(info.transfer or "")

    primary = _select_primary_audio_stream(info.audio)
    high = (primary.codec_name in HIGH_BITRATE_AUDIO_CODECS or
            (primary.bit_rate is not None and primary.bit_rate > HIGH_BITRATE_THRESHOLD_BPS))
    if high or (muxer == "mp4" and primary.codec_name not in MP4_AUDIO_COPY_OK):
        if primary.channels > 2:
            audio_args, audio_kbps = ["-c:a:0", "eac3", "-b:a:0", "384k"], 384
        else:
            audio_args, audio_kbps = ["-c:a:0", "aac", "-b:a:0", "192k", "-ac:0", "2"], 192
    else:
        audio_args = ["-c:a:0", "copy"]
        audio_kbps = primary.bit_rate // 1000 if primary.bit_rate else FALLBACK_AUDIO_KBPS_IF_UNKNOWN

    if muxer == "mp4":
        subs = [i for i, lang, codec in info.subs if lang in ("eng", "en") and codec == "mov_text"]
    else:
        subs = [i for i, lang, codec in info.subs if lang in ("eng", "en")]

    def budget(size_bytes: int) -> int:
        return int(size_bytes * 8 * 0.98 / info.duration_s / 1000 - audio_kbps)

    preferred, cap = budget(cfg.target_size_bytes), budget(opts["cap_bytes"])
    # Start at the smallest tier whose box already contains the source (never upscale,
    # and don't give a 720p source 1080p-tier bitrates); step down only if the size cap
    # cannot fund that tier's quality floor.
    start = 0
    for i, (_, mw, mh, *_rest) in enumerate(TIERS):
        if info.width <= mw * 1.05 and info.height <= mh * 1.05:
            start = i
    chosen = None
    for tier, mw, mh, floor, aim_sdr, aim_hdr, ceil_sdr, ceil_hdr in TIERS[start:]:
        ow, oh = _fit(info.width, info.height, mw, mh)
        kbps = min(max(preferred, aim_hdr if hdr else aim_sdr), cap, ceil_hdr if hdr else ceil_sdr)
        if kbps >= floor:
            chosen = (tier, ow, oh, kbps)
            break
    if chosen is None:
        tier, mw, mh = TIERS[-1][:3]
        ow, oh = _fit(info.width, info.height, mw, mh)
        chosen = (tier, ow, oh, max(min(preferred, cap), 250))
    tier, ow, oh, kbps = chosen
    predicted = int((kbps + audio_kbps) * 1000 / 8 * info.duration_s * 1.02)
    return Plan(tier=tier, out_w=ow, out_h=oh, video_kbps=kbps, hdr=hdr,
                audio_index=primary.index, audio_args=audio_args, audio_kbps=audio_kbps,
                sub_indices=subs, muxer=muxer, predicted_bytes=predicted)


def encode(src: Path, tmp: Path, plan: Plan, cfg: Config) -> None:
    fmt = "p010" if plan.hdr else "nv12"
    vf = f"scale_vaapi=w={plan.out_w}:h={plan.out_h}:format={fmt}"
    cmd = ["nice", "-n", str(cfg.nice_level), cfg.ffmpeg_bin, "-y", "-hide_banner", "-v", "error",
           "-hwaccel", "vaapi", "-hwaccel_output_format", "vaapi", "-vaapi_device", cfg.vaapi_device,
           "-i", str(src), "-map", "0:v:0", "-vf", vf, "-c:v", "hevc_vaapi",
           "-profile:v", "main10" if plan.hdr else "main",
           "-rc_mode", "VBR", "-b:v", f"{plan.video_kbps}k",
           "-maxrate", f"{int(plan.video_kbps * 1.5)}k", "-bufsize", f"{plan.video_kbps * 2}k"]
    if plan.hdr:
        cmd += ["-color_primaries", "bt2020", "-colorspace", "bt2020nc",
                "-color_trc", "smpte2084" if plan.hdr == "pq" else "arib-std-b67"]
    cmd += ["-map", f"0:a:{plan.audio_index}"] + plan.audio_args
    for i in plan.sub_indices:
        cmd += ["-map", f"0:s:{i}?"]
    if plan.sub_indices:
        cmd += ["-c:s", "copy"]
    cmd += ["-map_metadata", "0", "-map_chapters", "0"]
    if plan.muxer == "mp4":
        cmd += ["-tag:v", "hvc1", "-movflags", "+faststart"]
    cmd += ["-f", plan.muxer, str(tmp)]
    r = _run(cmd, timeout=8 * 3600)
    if r.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise SkipFile(f"encode failed: {r.stderr[-500:]}")


def verify(src: Path, tmp: Path, info: SrcInfo, plan: Plan, cfg: Config, opts: dict) -> str:
    if not tmp.exists():
        return "output missing"
    out_size, src_size = tmp.stat().st_size, src.stat().st_size
    if out_size < 50 * 1024 * 1024:
        return f"output implausibly small ({out_size} bytes)"
    if out_size > opts["cap_bytes"] * 1.05:
        return f"output {out_size} exceeds cap"
    if out_size > src_size * opts["max_output_fraction"]:
        return f"output {out_size} not meaningfully smaller than source {src_size}"
    try:
        o = probe_full(tmp, cfg)
    except SkipFile as exc:
        return f"output probe failed: {exc}"
    if o.vcodec != "hevc":
        return f"output codec {o.vcodec}"
    if abs(o.height - plan.out_h) > 2:
        return f"output height {o.height} != planned {plan.out_h}"
    if abs(o.duration_s - info.duration_s) > info.duration_s * cfg.duration_tolerance_fraction:
        return f"duration mismatch src={info.duration_s:.1f}s out={o.duration_s:.1f}s"
    if not o.audio:
        return "output has no audio"
    for frac in (0.1, 0.5, 0.9):
        r = _run([cfg.ffmpeg_bin, "-v", "error", "-ss", f"{o.duration_s * frac:.1f}", "-t", "8",
                  "-i", str(tmp), "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"], timeout=600)
        # Fail on a non-zero exit or genuine decoder errors. The null muxer's
        # "non monotonically increasing dts" notices after a seek are timestamp
        # bookkeeping, not corruption (pilot 2026-09-24 false positive on a good file).
        real = [l for l in r.stderr.splitlines()
                if l.strip() and "non monotonically increasing dts" not in l
                and "dmx: " not in l]
        if r.returncode != 0 or real:
            return f"decode spot-check failed at {int(frac * 100)}%: {' | '.join(real)[:200] or r.returncode}"
    return "ok"


def candidates(cfg: Config, opts: dict, state: dict, only: list[Path] | None, retry: bool):
    if only:
        paths = [p for p in only if p.is_file()]
    else:
        paths = []
        for root in (cfg.movies_archive_root, cfg.tv_archive_root):
            for dp, dn, fn in os.walk(root):
                dn[:] = [d for d in dn if not d.startswith(".") and not d.endswith(".trickplay")]
                for f in fn:
                    p = Path(dp) / f
                    if p.suffix.lower() in VIDEO_EXTS:
                        paths.append(p)
    out = []
    for p in paths:
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size <= opts["size_threshold_bytes"] and not only:
            continue
        prev = state.get(str(p))
        if prev and not retry and prev.get("status") in ("skipped", "failed") and prev.get("src_bytes") == size:
            continue
        out.append((size, p))
    out.sort(reverse=True)
    return [p for _, p in out]


def zfs_snapshot(opts: dict, logger: RunLogger) -> str:
    name = f"{opts['snapshot_dataset']}@archive-compact-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    r = _run(["zfs", "snapshot", name])
    if r.returncode != 0:
        raise RuntimeError(f"zfs snapshot failed: {r.stderr.strip()}")
    logger.record(event="snapshot_created", snapshot=name)
    cutoff = datetime.now() - timedelta(days=opts["snapshot_retention_days"])
    r = _run(["zfs", "list", "-H", "-t", "snapshot", "-o", "name", opts["snapshot_dataset"]])
    for s in r.stdout.split():
        tag = s.split("@", 1)[-1]
        if tag.startswith("archive-compact-"):
            try:
                ts = datetime.strptime(tag[len("archive-compact-"):], "%Y%m%d-%H%M%S")
            except ValueError:
                continue
            if ts < cutoff:
                d = _run(["zfs", "destroy", s])
                logger.record(event="snapshot_expired", snapshot=s, rc=d.returncode)
    return name


def load_opts(config_path: Path) -> dict:
    raw = json.loads(config_path.read_text())
    opts = dict(DEFAULTS)
    opts.update(raw.get("compact", {}))
    return opts


def run_compact(cfg: Config, opts: dict, execute: bool, max_files: int | None,
                only: list[Path] | None, retry: bool, no_snapshot: bool) -> dict:
    state_path = cfg.work_dir / "compact-state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    logger = RunLogger(cfg.log_dir)
    hh, mm = (int(x) for x in opts["deadline"].split(":"))
    now = datetime.now()
    deadline = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if deadline <= now:
        deadline += timedelta(days=1)
    summary = dict(mode="EXECUTE" if execute else "DRY RUN", considered=0, replaced=0, skipped=0,
                   failed=0, bytes_before=0, bytes_after=0, log_file=str(logger.path))
    snapshot = None
    cfg.work_dir.mkdir(parents=True, exist_ok=True)
    for src in candidates(cfg, opts, state, only, retry):
        if max_files is not None and summary["considered"] >= max_files:
            break
        if execute and datetime.now() >= deadline:
            logger.record(event="deadline_reached"); break
        summary["considered"] += 1
        rec = dict(path=str(src), src_bytes=src.stat().st_size)
        try:
            info = probe_full(src, cfg)
            plan = make_plan(src, info, cfg, opts)
            rec.update(plan=asdict(plan), src_res=f"{info.width}x{info.height}", src_codec=info.vcodec,
                       dv_profile=info.dv_profile)
            if plan.predicted_bytes > rec["src_bytes"] * opts["max_output_fraction"]:
                raise SkipFile("predicted output not meaningfully smaller than source")
            if not execute:
                rec.update(status="planned"); logger.record(event="plan", **rec)
                continue
            est_s = info.duration_s / 12  # conservative vs measured ~20x real time
            if datetime.now() + timedelta(seconds=est_s) > deadline:
                logger.record(event="would_overrun_deadline", path=str(src)); break
            st = src.stat()
            tmp = cfg.work_dir / f"compact-{os.getpid()}{src.suffix.lower()}"
            t0 = time.time()
            encode(src, tmp, plan, cfg)
            verdict = verify(src, tmp, info, plan, cfg, opts)
            if verdict != "ok":
                tmp.unlink(missing_ok=True)
                raise RuntimeError(f"verification failed: {verdict}")
            st2 = src.stat()
            if (st2.st_size, st2.st_mtime_ns) != (st.st_size, st.st_mtime_ns):
                tmp.unlink(missing_ok=True)
                raise RuntimeError("source changed during encode; not replaced")
            if snapshot is None and not no_snapshot:
                snapshot = zfs_snapshot(opts, logger)
            os.chown(tmp, st.st_uid, st.st_gid)
            os.chmod(tmp, st.st_mode & 0o7777)
            out_bytes = tmp.stat().st_size
            os.replace(tmp, src)
            rec.update(status="replaced", out_bytes=out_bytes, encode_s=round(time.time() - t0),
                       snapshot=snapshot)
            summary["replaced"] += 1
            summary["bytes_before"] += rec["src_bytes"]
            summary["bytes_after"] += out_bytes
        except SkipFile as exc:
            rec.update(status="skipped", reason=str(exc)); summary["skipped"] += 1
        except Exception as exc:  # noqa: BLE001 - record and continue with the next file
            rec.update(status="failed", reason=str(exc)[:500]); summary["failed"] += 1
        rec["time"] = datetime.now(timezone.utc).isoformat()
        logger.record(event="file", **rec)
        if rec["status"] in ("replaced", "skipped", "failed"):
            state[str(src)] = {k: rec.get(k) for k in ("status", "reason", "src_bytes", "out_bytes", "time")}
            tmp_state = state_path.with_suffix(".tmp")
            tmp_state.write_text(json.dumps(state, indent=1))
            os.replace(tmp_state, state_path)
        log.info("%s %s %s", rec["status"], src, rec.get("reason", ""))
    if execute and summary["replaced"]:
        try:
            from .jellyfin_client import JellyfinClient
            JellyfinClient(cfg.jellyfin_url, cfg.jellyfin_api_key, cfg.jellyfin_scan_task_id).refresh_all_libraries()
            logger.record(event="jellyfin_scan_requested")
        except Exception as exc:  # noqa: BLE001
            logger.record(event="jellyfin_scan_failed", error=str(exc)[:300])
    logger.record(event="summary", **summary)
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Re-encode oversized archive files in place (dry run by default).")
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--max-files", type=int, default=None)
    ap.add_argument("--paths", type=Path, nargs="*", help="Only these files (pilot use)")
    ap.add_argument("--retry", action="store_true", help="Retry files previously skipped/failed")
    ap.add_argument("--no-snapshot", action="store_true")
    ap.add_argument("--wait-lock-minutes", type=int, default=90)
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = Config.load(a.config)
    opts = load_opts(a.config)
    waited = 0
    while True:
        try:
            with run_lock(cfg.lock_file):
                s = run_compact(cfg, opts, a.execute, a.max_files, a.paths, a.retry, a.no_snapshot)
            break
        except LockHeldError:
            if waited >= a.wait_lock_minutes:
                logging.error("archiver lock still held after %d min; giving up this run", waited)
                return 1
            time.sleep(60); waited += 1
    gb = lambda b: b / 1e9
    print(f"[{s['mode']}] considered {s['considered']}, replaced {s['replaced']}, skipped {s['skipped']}, "
          f"failed {s['failed']}; {gb(s['bytes_before']):.1f} GB -> {gb(s['bytes_after']):.1f} GB")
    print(f"Log: {s['log_file']}")
    return 0 if s["failed"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
