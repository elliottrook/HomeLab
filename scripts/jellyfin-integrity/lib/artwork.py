"""Embedded cover-art extractor: FLAC PICTURE blocks, MP3 APIC frames,
MP4/M4A covr atoms. Purely additive — only ever writes a new cover.jpg/png
file, never modifies or deletes an existing one.
"""
import os


def find_albums_missing_art(jf, music_library_id, translator):
    albums = jf.get_library_items(music_library_id, "MusicAlbum", ["Path"])
    missing = []
    for album in albums:
        container_path = album.get("Path")
        if not container_path:
            continue
        try:
            host_path = translator.to_host(container_path)
        except Exception:
            continue
        if not os.path.isdir(host_path):
            continue
        if not any(f.lower() in ("cover.jpg", "cover.png", "folder.jpg", "folder.png")
                   for f in os.listdir(host_path)):
            missing.append({"album_id": album.get("Id"), "name": album.get("Name"),
                             "host_path": host_path})
    return missing


def _extract_flac_picture(path):
    with open(path, "rb") as f:
        if f.read(4) != b"fLaC":
            return None
        while True:
            header = f.read(4)
            if len(header) < 4:
                return None
            is_last = header[0] & 0x80
            block_type = header[0] & 0x7F
            block_len = int.from_bytes(header[1:4], "big")
            block = f.read(block_len)
            if block_type == 6:  # PICTURE
                pos = 4  # picture type
                mime_len = int.from_bytes(block[pos:pos + 4], "big"); pos += 4
                mime = block[pos:pos + mime_len].decode("ascii", "replace"); pos += mime_len
                desc_len = int.from_bytes(block[pos:pos + 4], "big"); pos += 4
                pos += desc_len  # description
                pos += 16  # width, height, depth, colors (4 x 4 bytes)
                data_len = int.from_bytes(block[pos:pos + 4], "big"); pos += 4
                data = block[pos:pos + data_len]
                return mime, data
            if is_last:
                return None


def _extract_mp3_apic(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[0:3] != b"ID3":
        return None
    major = data[3]
    size = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | \
           ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
    pos = 10
    end = 10 + size
    while pos < end - 10:
        if major >= 3:
            frame_id = data[pos:pos + 4]
            frame_size = int.from_bytes(data[pos + 4:pos + 8], "big")
            frame_start = pos + 10
        else:  # ID3v2.2 uses 3-char frame IDs, 3-byte sizes
            frame_id = data[pos:pos + 3]
            frame_size = int.from_bytes(data[pos + 3:pos + 6], "big")
            frame_start = pos + 6
        if frame_size <= 0 or frame_id in (b"\x00\x00\x00\x00", b"\x00\x00\x00"):
            break
        if frame_id in (b"APIC", b"PIC"):
            body = data[frame_start:frame_start + frame_size]
            encoding = body[0]
            rest = body[1:]
            if frame_id == b"APIC":
                mime_end = rest.index(b"\x00")
                mime = rest[:mime_end].decode("ascii", "replace")
                rest = rest[mime_end + 1:]
            else:
                mime = {"JPG": "image/jpeg", "PNG": "image/png"}.get(
                    rest[:3].decode("ascii", "replace"), "image/jpeg")
                rest = rest[3:]
            rest = rest[1:]  # picture type byte
            desc_term = b"\x00\x00" if encoding in (1, 2) else b"\x00"
            desc_end = rest.index(desc_term)
            img_data = rest[desc_end + len(desc_term):]
            return mime, img_data
        pos = frame_start + frame_size
    return None


def _extract_mp4_cover(path):
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
        return None
    udta = find_atom(data, b"udta", *moov)
    if not udta:
        return None
    meta = find_atom(data, b"meta", *udta)
    if not meta:
        return None
    ilst = find_atom(data, b"ilst", meta[0] + 4, meta[1])  # meta has a 4-byte version/flags header
    if not ilst:
        return None
    covr = find_atom(data, b"covr", *ilst)
    if not covr:
        return None
    # covr contains one or more 'data' sub-atoms
    data_atom = find_atom(data, b"data", *covr)
    if not data_atom:
        return None
    payload = data[data_atom[0] + 8:data_atom[1]]  # skip 8-byte data-atom flags/reserved
    mime = "image/png" if payload[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
    return mime, payload


def extract_cover(album_track_paths):
    """Try each track in an album until one yields embedded art.
    Returns (mime, bytes) or None.
    """
    for track_path in album_track_paths:
        lower = track_path.lower()
        try:
            if lower.endswith(".flac"):
                result = _extract_flac_picture(track_path)
            elif lower.endswith(".mp3"):
                result = _extract_mp3_apic(track_path)
            elif lower.endswith((".m4a", ".mp4")):
                result = _extract_mp4_cover(track_path)
            else:
                result = None
        except Exception:
            result = None
        if result:
            return result
    return None


def write_cover(album_host_path, mime, image_bytes):
    ext = "png" if "png" in mime else "jpg"
    dest = os.path.join(album_host_path, f"cover.{ext}")
    with open(dest, "wb") as f:
        f.write(image_bytes)
    return dest
