"""Build neutral rounded UI masks; existing Aster brand artwork is untouched."""
from pathlib import Path
import math
import struct
import zlib


def png(path, width, height, radius, stroke=0, inverse=False):
    def coverage(x, y, inset=0):
        r = max(0, radius - inset)
        if r == 0:
            return float(inset <= x <= width - inset and inset <= y <= height - inset)
        cx = min(max(x, inset + r), width - inset - r)
        cy = min(max(y, inset + r), height - inset - r)
        distance = math.hypot(x - cx, y - cy) - r
        return max(0, min(1, 0.5 - distance))

    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            alpha = coverage(x + 0.5, y + 0.5)
            if stroke:
                alpha -= coverage(x + 0.5, y + 0.5, stroke)
            if inverse:
                alpha = 1 - alpha
            rows.extend((255, 255, 255, round(max(0, alpha) * 255)))

    def chunk(kind, data):
        return (struct.pack('!I', len(data)) + kind + data
                + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff))

    path.write_bytes(b'\x89PNG\r\n\x1a\n'
                     + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 6, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(bytes(rows), 9))
                     + chunk(b'IEND', b''))


if __name__ == '__main__':
    media = Path(__file__).resolve().parents[1] / 'media'
    for name, width, height, radius, stroke in (
        ('ui-solid', 2, 2, 0, 0),
        ('ui-card-mask', 400, 225, 18, 0),
        ('ui-card-ring', 400, 225, 18, 3),
        ('ui-hero-mask', 1836, 420, 24, 0),
        ('ui-rail-mask', 250, 1080, 20, 0),
        ('ui-rail-collapsed-mask', 84, 1080, 18, 0),
        ('ui-panel', 64, 64, 20, 0),
        ('ui-progress', 16, 8, 4, 0),
    ):
        png(media / (name + '.png'), width, height, radius, stroke)
    png(media / 'ui-card-corners.png', 400, 225, 18, inverse=True)
    png(media / 'ui-hero-corners.png', 1680, 400, 24, inverse=True)
