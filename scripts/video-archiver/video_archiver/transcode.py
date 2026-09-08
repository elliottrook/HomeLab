from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import Config

log = logging.getLogger("video_archiver.transcode")

# (max_width, max_height, min_acceptable_video_kbps), highest quality first.
RESOLUTION_LADDER = [
    (1920, 1080, 1200),
    (1280, 720, 700),
    (854, 480, 400),
]

# Codecs treated as "large" regardless of reported bit_rate — lossless/near-lossless
# tracks that would eat the whole size budget if copied through unchanged.
HIGH_BITRATE_AUDIO_CODECS = {"truehd", "dts", "flac", "pcm_s16le", "pcm_s24le", "pcm_s32le", "mlp"}
HIGH_BITRATE_THRESHOLD_BPS = 640_000
FALLBACK_AUDIO_KBPS_IF_UNKNOWN = 160


class TranscodeError(RuntimeError):
    pass


@dataclass
class AudioStreamInfo:
    index: int
    codec_name: str
    channels: int
    bit_rate: int | None


@dataclass
class Probe:
    duration_s: float
    width: int
    height: int
    audio_streams: list[AudioStreamInfo]
    has_subtitles: bool


@dataclass
class BitratePlan:
    video_kbps: int
    max_width: int
    max_height: int
    below_quality_floor: bool
    audio_plan: list[tuple[int, str]]  # (stream_index_in_output_order, "copy" | "aac" | "eac3")


def _run(cmd: list[str], timeout_s: int | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)


def probe(path: Path, config: Config) -> Probe:
    result = _run(
        [
            config.ffprobe_bin,
            "-v", "error",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        timeout_s=120,
    )
    if result.returncode != 0:
        raise TranscodeError(f"ffprobe failed for {path}: {result.stderr[:500]}")

    data = json.loads(result.stdout)
    duration_s = float(data["format"]["duration"])

    width = height = 0
    audio_streams: list[AudioStreamInfo] = []
    has_subtitles = False

    for stream in data.get("streams", []):
        codec_type = stream.get("codec_type")
        if codec_type == "video" and not width:
            width = int(stream.get("width", 0))
            height = int(stream.get("height", 0))
        elif codec_type == "audio":
            bit_rate = stream.get("bit_rate")
            audio_streams.append(
                AudioStreamInfo(
                    index=len(audio_streams),
                    codec_name=stream.get("codec_name", ""),
                    channels=int(stream.get("channels", 2)),
                    bit_rate=int(bit_rate) if bit_rate is not None else None,
                )
            )
        elif codec_type == "subtitle":
            has_subtitles = True

    if not width or not duration_s:
        raise TranscodeError(f"ffprobe returned no usable video/duration data for {path}")

    return Probe(duration_s=duration_s, width=width, height=height,
                 audio_streams=audio_streams, has_subtitles=has_subtitles)


def compute_bitrate_plan(probe_result: Probe, config: Config) -> BitratePlan:
    audio_plan: list[tuple[int, str]] = []
    reserved_audio_kbps = 0

    for stream in probe_result.audio_streams:
        is_high_bitrate = (
            stream.codec_name in HIGH_BITRATE_AUDIO_CODECS
            or (stream.bit_rate is not None and stream.bit_rate > HIGH_BITRATE_THRESHOLD_BPS)
        )
        if is_high_bitrate:
            mode = "eac3" if stream.channels > 2 else "aac"
            reserved_audio_kbps += 384 if stream.channels > 2 else 192
        else:
            mode = "copy"
            reserved_audio_kbps += (
                stream.bit_rate // 1000 if stream.bit_rate else FALLBACK_AUDIO_KBPS_IF_UNKNOWN
            )
        audio_plan.append((stream.index, mode))

    usable_kbps = (config.target_size_bytes * 8 * 0.98) / probe_result.duration_s / 1000
    video_kbps = max(int(usable_kbps - reserved_audio_kbps), 100)

    max_width = max_height = None
    below_floor = True
    for ladder_w, ladder_h, floor_kbps in RESOLUTION_LADDER:
        if video_kbps >= floor_kbps:
            max_width, max_height = ladder_w, ladder_h
            below_floor = False
            break
    if max_width is None:
        max_width, max_height, _ = RESOLUTION_LADDER[-1]

    return BitratePlan(
        video_kbps=video_kbps,
        max_width=max_width,
        max_height=max_height,
        below_quality_floor=below_floor,
        audio_plan=audio_plan,
    )


def _audio_codec_args(audio_plan: list[tuple[int, str]]) -> list[str]:
    args: list[str] = []
    for idx, mode in audio_plan:
        if mode == "copy":
            args += [f"-c:a:{idx}", "copy"]
        elif mode == "aac":
            args += [f"-c:a:{idx}", "aac", f"-b:a:{idx}", "192k", f"-ac:{idx}", "2"]
        elif mode == "eac3":
            args += [f"-c:a:{idx}", "eac3", f"-b:a:{idx}", "384k"]
    return args


def transcode(src: Path, dst_tmp: Path, plan: BitratePlan, config: Config) -> None:
    """Hardware-accelerated encode via Intel Quick Sync (VAAPI, hevc_vaapi), through the
    already-running jellyfin container which already has /dev/dri passed through for its own
    hardware transcoding. Confirmed by direct testing on 2026-09-07: ~21.6x real-time (a ~54
    min 1080p episode in ~2.5 min), versus ~1h40m+ for a software libx265 encode of the same
    file — the difference between practical and impractical for a whole-library job. This
    supersedes this project's original "no GPU exists in the lab" design assumption; an Intel
    Arc A380 landed on this host since that was written.

    -rc_mode VBR with -maxrate/-bufsize is required, not optional: confirmed by testing that
    hevc_vaapi's default rate control mode ignores -b:v and produces output many times larger
    than the target (30 Mbps against a 3.3 Mbps target in one test) without it."""
    dst_tmp.parent.mkdir(parents=True, exist_ok=True)

    scale_filter = f"scale_vaapi=w=min(iw\\,{plan.max_width}):h=min(ih\\,{plan.max_height})"
    nice_prefix = ["nice", "-n", str(config.nice_level)]

    def build(include_subs: bool) -> list[str]:
        cmd = nice_prefix + [
            config.ffmpeg_bin, "-y",
            "-hwaccel", "vaapi", "-hwaccel_output_format", "vaapi",
            "-vaapi_device", config.vaapi_device,
            "-i", str(src),
            "-map", "0:v:0", "-vf", scale_filter,
            "-c:v", "hevc_vaapi",
            "-rc_mode", "VBR",
            "-b:v", f"{plan.video_kbps}k",
            "-maxrate", f"{int(plan.video_kbps * 1.5)}k",
            "-bufsize", f"{plan.video_kbps * 2}k",
            "-map", "0:a?",
        ] + _audio_codec_args(plan.audio_plan)
        if include_subs:
            cmd += ["-map", "0:s?", "-c:s", "copy"]
        # Explicit output format as a backstop: don't rely solely on dst_tmp's extension
        # for muxer auto-detection (a ".partial"-suffixed name broke this once already).
        cmd += ["-f", "matroska", str(dst_tmp)]
        return cmd

    result = _run(build(include_subs=True), timeout_s=6 * 3600)
    if result.returncode != 0:
        log.warning("encode with subtitles failed for %s, retrying without subtitle streams", src)
        dst_tmp.unlink(missing_ok=True)
        result = _run(build(include_subs=False), timeout_s=6 * 3600)
        if result.returncode != 0:
            dst_tmp.unlink(missing_ok=True)
            raise TranscodeError(f"ffmpeg encode failed for {src}: {result.stderr[-800:]}")


def verify_output(dst_tmp: Path, src_duration_s: float, config: Config) -> tuple[bool, str]:
    if not dst_tmp.exists() or dst_tmp.stat().st_size < 10 * 1024 * 1024:
        return False, "output missing or implausibly small"

    if dst_tmp.stat().st_size > config.target_size_max_bytes * 1.10:
        return False, "output larger than the configured maximum size (with 10% tolerance)"

    try:
        out_probe = probe(dst_tmp, config)
    except TranscodeError as exc:
        return False, f"output failed to probe cleanly: {exc}"

    tolerance = src_duration_s * config.duration_tolerance_fraction
    if abs(out_probe.duration_s - src_duration_s) > tolerance:
        return False, (
            f"duration mismatch: source={src_duration_s:.1f}s output={out_probe.duration_s:.1f}s"
        )

    return True, "ok"
