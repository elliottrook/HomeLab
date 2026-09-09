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
    is_default: bool
    language: str | None


@dataclass
class SubtitleStreamInfo:
    index: int
    language: str | None


@dataclass
class Probe:
    duration_s: float
    width: int
    height: int
    audio_streams: list[AudioStreamInfo]
    subtitle_streams: list[SubtitleStreamInfo]


@dataclass
class BitratePlan:
    video_kbps: int
    max_width: int
    max_height: int
    below_quality_floor: bool
    # The single audio stream kept, addressed by its INPUT position (0:a:N) -- always
    # mapped to output position 0, since it's the only audio stream in the output.
    selected_audio_input_index: int
    audio_mode: str  # "copy" | "aac" | "eac3"
    dropped_audio_track_count: int
    # English-language subtitle streams (INPUT positions, 0:s:N) to keep, unlike audio
    # every one of these is kept rather than picking just one -- subtitles are
    # negligible size, so there's no budget reason to drop extras (e.g. a plain track
    # plus an SDH one). Added 2026-09-08 (Jason's request): previously mapped ALL
    # subtitle tracks regardless of language, same over-inclusive pattern as audio had.
    english_subtitle_indices: list[int]


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
    subtitle_streams: list[SubtitleStreamInfo] = []

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
                    is_default=bool(stream.get("disposition", {}).get("default")),
                    language=stream.get("tags", {}).get("language"),
                )
            )
        elif codec_type == "subtitle":
            subtitle_streams.append(
                SubtitleStreamInfo(
                    index=len(subtitle_streams),
                    language=stream.get("tags", {}).get("language"),
                )
            )

    if not width or not duration_s:
        raise TranscodeError(f"ffprobe returned no usable video/duration data for {path}")

    return Probe(duration_s=duration_s, width=width, height=height,
                 audio_streams=audio_streams, subtitle_streams=subtitle_streams)


def _select_primary_audio_stream(audio_streams: list[AudioStreamInfo]) -> AudioStreamInfo:
    """Pick exactly one audio stream to keep: the source's own flagged default track,
    else the first English track, else just the first stream. Added 2026-09-08 after a
    real 11-audio-track multi-language REMUX ("Ready or Not: Here I Come") blew the
    entire size budget on reserved audio bitrate alone -- the old design mapped and
    budgeted for every audio stream regardless of count, which floored video bitrate to
    the 100kbps minimum and then still failed the output-size check, because several
    tracks were "copy" mode (passed through at their original multi-hundred-kbps
    bitrate) rather than actually constrained by that reservation. A personal archive
    doesn't need 5+ foreign-language 5.1 tracks preserved at full bitrate alongside the
    one actually watched (Jason's call, 2026-09-08: keep default/English only, drop the
    rest entirely rather than trying to fit a capped/prioritized subset)."""
    for stream in audio_streams:
        if stream.is_default:
            return stream
    for stream in audio_streams:
        if stream.language == "eng":
            return stream
    return audio_streams[0]


def compute_bitrate_plan(probe_result: Probe, config: Config) -> BitratePlan:
    if not probe_result.audio_streams:
        raise TranscodeError("source has no audio streams to select from")

    primary = _select_primary_audio_stream(probe_result.audio_streams)
    dropped_audio_track_count = len(probe_result.audio_streams) - 1

    is_high_bitrate = (
        primary.codec_name in HIGH_BITRATE_AUDIO_CODECS
        or (primary.bit_rate is not None and primary.bit_rate > HIGH_BITRATE_THRESHOLD_BPS)
    )
    if is_high_bitrate:
        audio_mode = "eac3" if primary.channels > 2 else "aac"
        reserved_audio_kbps = 384 if primary.channels > 2 else 192
    else:
        audio_mode = "copy"
        reserved_audio_kbps = (
            primary.bit_rate // 1000 if primary.bit_rate else FALLBACK_AUDIO_KBPS_IF_UNKNOWN
        )

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

    english_subtitle_indices = [
        s.index for s in probe_result.subtitle_streams if s.language in ("eng", "en")
    ]

    return BitratePlan(
        video_kbps=video_kbps,
        max_width=max_width,
        max_height=max_height,
        below_quality_floor=below_floor,
        selected_audio_input_index=primary.index,
        audio_mode=audio_mode,
        dropped_audio_track_count=dropped_audio_track_count,
        english_subtitle_indices=english_subtitle_indices,
    )


def _audio_codec_args(mode: str) -> list[str]:
    # Output audio position is always 0: exactly one audio stream is ever mapped now
    # (see BitratePlan.selected_audio_input_index), regardless of its position in the
    # source.
    if mode == "copy":
        return ["-c:a:0", "copy"]
    elif mode == "aac":
        return ["-c:a:0", "aac", "-b:a:0", "192k", "-ac:0", "2"]
    elif mode == "eac3":
        return ["-c:a:0", "eac3", "-b:a:0", "384k"]
    raise TranscodeError(f"unknown audio mode: {mode}")


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
            "-map", f"0:a:{plan.selected_audio_input_index}",
        ] + _audio_codec_args(plan.audio_mode)
        if include_subs:
            for sub_idx in plan.english_subtitle_indices:
                cmd += ["-map", f"0:s:{sub_idx}?"]
            if plan.english_subtitle_indices:
                cmd += ["-c:s", "copy"]
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
