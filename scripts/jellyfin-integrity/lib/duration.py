"""From-scratch FLAC/MP3/M4A duration readers, standard-library only.

No ffprobe/mutagen dependency by design (both were removed from TrueNAS
during the Plex-to-Jellyfin cleanup and should not be reintroduced).
"""
import struct

# MPEG audio frame tables, keyed [version_index][layer_index]
# version_index: 0=MPEG2.5, 2=MPEG2, 3=MPEG1 (1 is reserved)
# layer_index: 1=Layer III, 2=Layer II, 3=Layer I (0 is reserved)
_BITRATES = {
    3: {  # MPEG1
        3: [0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448],  # Layer I
        2: [0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384],      # Layer II
        1: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320],       # Layer III
    },
    2: {  # MPEG2 / 2.5 share the same low-bitrate table
        3: [0, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256],
        2: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
        1: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160],
    },
}
_BITRATES[0] = _BITRATES[2]  # MPEG2.5 uses the MPEG2 low tables

_SAMPLERATES = {
    3: [44100, 48000, 32000],  # MPEG1
    2: [22050, 24000, 16000],  # MPEG2
    0: [11025, 12000, 8000],   # MPEG2.5
}

# Samples per frame, keyed [version_index][layer_index]
_SAMPLES_PER_FRAME = {
    3: {3: 384, 2: 1152, 1: 1152},  # MPEG1: LayerI, LayerII, LayerIII
    2: {3: 384, 2: 1152, 1: 576},   # MPEG2
    0: {3: 384, 2: 1152, 1: 576},   # MPEG2.5
}


class DurationError(Exception):
    pass


def read_duration(path):
    """Return duration in seconds (float) for a .flac/.mp3/.m4a|.mp4 file."""
    lower = path.lower()
    if lower.endswith(".flac"):
        return _flac_duration(path)
    if lower.endswith(".mp3"):
        return _mp3_duration(path)
    if lower.endswith((".m4a", ".mp4", ".alac")):
        return _mp4_duration(path)
    raise DurationError(f"unsupported extension: {path}")


def _flac_duration(path):
    with open(path, "rb") as f:
        magic = f.read(4)
        if magic != b"fLaC":
            raise DurationError(f"not a FLAC file: {path}")
        while True:
            header = f.read(4)
            if len(header) < 4:
                raise DurationError(f"FLAC ended before STREAMINFO: {path}")
            is_last = header[0] & 0x80
            block_type = header[0] & 0x7F
            block_len = int.from_bytes(header[1:4], "big")
            block = f.read(block_len)
            if block_type == 0:  # STREAMINFO
                # bytes: min/max blocksize(2+2), min/max framesize(3+3),
                # then 20 bits sample rate, 3 bits channels-1, 5 bits bps-1,
                # 36 bits total samples, 16 bytes MD5
                if len(block) < 18:
                    raise DurationError(f"truncated STREAMINFO: {path}")
                tail = block[10:18]
                bits = int.from_bytes(tail, "big")  # 64 bits
                sample_rate = (bits >> 44) & 0xFFFFF
                total_samples = bits & 0xFFFFFFFFF  # low 36 bits
                if sample_rate == 0:
                    raise DurationError(f"zero sample rate: {path}")
                return total_samples / sample_rate
            if is_last:
                break
        raise DurationError(f"no STREAMINFO block found: {path}")


def _mp3_duration(path):
    with open(path, "rb") as f:
        data = f.read()

    pos = 0
    n = len(data)

    # Skip leading ID3v2 tag if present.
    if data[0:3] == b"ID3":
        size = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | \
               ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
        pos = 10 + size

    # Trailing ID3v1 tag (128 bytes, "TAG" magic) — exclude from scan range.
    end = n
    if n >= 128 and data[n - 128:n - 125] == b"TAG":
        end = n - 128

    total_duration = 0.0
    frames_seen = 0

    while pos < end - 4:
        if data[pos] != 0xFF or (data[pos + 1] & 0xE0) != 0xE0:
            pos += 1
            continue

        b1 = data[pos + 1]
        b2 = data[pos + 2]

        version_bits = (b1 >> 3) & 0x03
        layer_bits = (b1 >> 1) & 0x03
        bitrate_idx = (b2 >> 4) & 0x0F
        samplerate_idx = (b2 >> 2) & 0x03
        padding = (b2 >> 1) & 0x01

        if version_bits == 1 or layer_bits == 0 or bitrate_idx in (0, 15) or samplerate_idx == 3:
            pos += 1  # not a valid frame header, resync
            continue

        try:
            bitrate_kbps = _BITRATES[version_bits][layer_bits][bitrate_idx]
            sample_rate = _SAMPLERATES[version_bits][samplerate_idx]
            samples_per_frame = _SAMPLES_PER_FRAME[version_bits][layer_bits]
        except (KeyError, IndexError):
            pos += 1
            continue

        if bitrate_kbps == 0 or sample_rate == 0:
            pos += 1
            continue

        bitrate_bps = bitrate_kbps * 1000

        if layer_bits == 1:  # Layer III
            if version_bits == 3:  # MPEG1
                frame_len = (144 * bitrate_bps) // sample_rate + padding
            else:  # MPEG2 / 2.5
                frame_len = (72 * bitrate_bps) // sample_rate + padding
        elif layer_bits == 2:  # Layer II
            frame_len = (144 * bitrate_bps) // sample_rate + padding
        else:  # Layer I
            frame_len = ((12 * bitrate_bps) // sample_rate + padding) * 4

        if frame_len <= 0:
            pos += 1
            continue

        total_duration += samples_per_frame / sample_rate
        frames_seen += 1
        pos += frame_len

    if frames_seen == 0:
        raise DurationError(f"no valid MPEG frames found: {path}")

    return total_duration


def _mp4_duration(path):
    with open(path, "rb") as f:
        data = f.read()

    def find_atom(buf, name, start=0, end=None):
        end = len(buf) if end is None else end
        pos = start
        while pos + 8 <= end:
            size = int.from_bytes(buf[pos:pos + 4], "big")
            atype = buf[pos + 4:pos + 8]
            header_len = 8
            if size == 1:
                size = int.from_bytes(buf[pos + 8:pos + 16], "big")
                header_len = 16
            if size == 0:
                size = end - pos
            if atype == name:
                return pos + header_len, pos + size
            pos += size
        return None

    moov = find_atom(data, b"moov")
    if not moov:
        raise DurationError(f"no moov atom: {path}")
    mvhd = find_atom(data, b"mvhd", moov[0], moov[1])
    if not mvhd:
        raise DurationError(f"no mvhd atom: {path}")

    body_start = mvhd[0]
    version = data[body_start]
    if version == 1:
        timescale = int.from_bytes(data[body_start + 20:body_start + 24], "big")
        duration = int.from_bytes(data[body_start + 24:body_start + 32], "big")
    else:
        timescale = int.from_bytes(data[body_start + 12:body_start + 16], "big")
        duration = int.from_bytes(data[body_start + 16:body_start + 20], "big")

    if timescale == 0:
        raise DurationError(f"zero timescale: {path}")

    return duration / timescale
