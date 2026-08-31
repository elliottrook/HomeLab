from __future__ import annotations

import json
import logging
import subprocess
import uuid
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


def transcode_2pass(src: Path, dst_tmp: Path, plan: BitratePlan, config: Config) -> None:
    dst_tmp.parent.mkdir(parents=True, exist_ok=True)
    config.work_dir.mkdir(parents=True, exist_ok=True)
    passlog_prefix = config.work_dir / f"ffmpeg2pass-{uuid.uuid4().hex}"

    scale_filter = (
        f"scale='min(iw,{plan.max_width})':'min(ih,{plan.max_height})':"
        f"force_original_aspect_ratio=decrease:force_divisible_by=2"
    )
    nice_prefix = ["nice", "-n", str(config.nice_level)]

    base = nice_prefix + [
        config.ffmpeg_bin, "-y", "-i", str(src),
        "-map", "0:v:0", "-vf", scale_filter,
        "-c:v", "libx265", "-b:v", f"{plan.video_kbps}k",
        "-preset", "medium",
    ]

    pass1 = base + [
        "-x265-params", f"pass=1:log-level=error",
        "-passlogfile", str(passlog_prefix),
        "-an", "-sn", "-f", "null", "/dev/null" if _is_posix() else "NUL",
    ]
    result = _run(pass1, timeout_s=6 * 3600)
    if result.returncode != 0:
        raise TranscodeError(f"ffmpeg pass 1 failed for {src}: {result.stderr[-800:]}")

    def build_pass2(include_subs: bool) -> list[str]:
        cmd = base + [
            "-x265-params", f"pass=2:log-level=error",
            "-passlogfile", str(passlog_prefix),
            "-map", "0:a?",
        ] + _audio_codec_args(plan.audio_plan)
        if include_subs:
            cmd += ["-map", "0:s?", "-c:s", "copy"]
        cmd += [str(dst_tmp)]
        return cmd

    result = _run(build_pass2(include_subs=True), timeout_s=6 * 3600)
    if result.returncode != 0:
        log.warning("pass 2 with subtitles failed for %s, retrying without subtitle streams", src)
        dst_tmp.unlink(missing_ok=True)
        result = _run(build_pass2(include_subs=False), timeout_s=6 * 3600)
        if result.returncode != 0:
            dst_tmp.unlink(missing_ok=True)
            raise TranscodeError(f"ffmpeg pass 2 failed for {src}: {result.stderr[-800:]}")

    for suffix in ("-0.log", "-0.log.mbtree"):
        Path(str(passlog_prefix) + suffix).unlink(missing_ok=True)


def _is_posix() -> bool:
    import os
    return os.name == "posix"


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
