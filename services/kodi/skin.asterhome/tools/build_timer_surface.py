"""Build the transparent Aster timer base without platform thumbnail tools."""
from pathlib import Path
import math
import struct
import zlib


SIZE = 560
CENTRE = SIZE / 2


def circle_coverage(x, y, radius):
    distance = math.hypot(x - CENTRE, y - CENTRE)
    return max(0.0, min(1.0, radius + 0.5 - distance))


def render(path):
    rows = bytearray()
    for y in range(SIZE):
        rows.append(0)
        for x in range(SIZE):
            outer = circle_coverage(x + 0.5, y + 0.5, 222)
            ring = max(0.0, circle_coverage(x + 0.5, y + 0.5, 203.5)
                       - circle_coverage(x + 0.5, y + 0.5, 200.5))
            base = (41, 44, 43)
            accent = (155, 201, 168)
            alpha = max(outer, ring * 0.20)
            blend = ring * 0.20
            colour = tuple(round(base[index] * (1 - blend) + accent[index] * blend)
                           for index in range(3))
            rows.extend((*colour, round(alpha * 255)))

    def chunk(kind, data):
        return (struct.pack('!I', len(data)) + kind + data
                + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff))

    path.write_bytes(b'\x89PNG\r\n\x1a\n'
                     + chunk(b'IHDR', struct.pack('!2I5B', SIZE, SIZE, 8, 6, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(bytes(rows), 9))
                     + chunk(b'IEND', b''))


if __name__ == '__main__':
    render(Path(__file__).resolve().parents[1] / 'media' / 'ui-timer-base.png')
