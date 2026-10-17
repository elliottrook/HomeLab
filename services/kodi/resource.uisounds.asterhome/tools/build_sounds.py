#!/usr/bin/env python3
"""Build the original Aster Home UI click family using only the stdlib."""

from __future__ import annotations

import math
import random
import shutil
import struct
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RATE = 48_000


def click(path: Path, *, frequency: float, duration: float = 0.045,
          left: float = 0.15, right: float = 0.15, second: float | None = None) -> None:
    """Write a quiet, dry stereo click with no sustained or sweeping component."""
    rng = random.Random(path.name)
    frames = []
    count = round(RATE * duration)
    for index in range(count):
        t = index / RATE
        attack = min(1.0, t / 0.0007)
        body = math.exp(-92.0 * t)
        sample = attack * body * (
            0.70 * math.sin(2.0 * math.pi * frequency * t)
            + 0.18 * math.sin(2.0 * math.pi * frequency * 2.13 * t)
            + 0.08 * (rng.random() * 2.0 - 1.0)
        )
        if second is not None and t >= 0.026:
            t2 = t - 0.026
            sample += 0.38 * math.exp(-115.0 * t2) * math.sin(
                2.0 * math.pi * second * t2)
        frames.append(struct.pack('<hh',
                                  round(max(-1.0, min(1.0, sample * left)) * 32767),
                                  round(max(-1.0, min(1.0, sample * right)) * 32767)))
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(b''.join(frames))


def main() -> None:
    resources = ROOT / 'resources'
    resources.mkdir(parents=True, exist_ok=True)
    # Horizontal actions are deliberately weighted toward the destination.
    click(resources / 'nav-left.wav', frequency=930, left=0.18, right=0.055)
    click(resources / 'nav-right.wav', frequency=930, left=0.055, right=0.18)
    # Vertical motion uses a restrained pitch cue because stereo has no height axis.
    click(resources / 'nav-up.wav', frequency=1160, left=0.13, right=0.13)
    click(resources / 'nav-down.wav', frequency=760, left=0.13, right=0.13)
    click(resources / 'select.wav', frequency=680, duration=0.065,
          left=0.17, right=0.17, second=1080)
    click(resources / 'back.wav', frequency=620, duration=0.075,
          left=0.13, right=0.13, second=470)
    click(resources / 'notify.wav', frequency=820, duration=0.085,
          left=0.14, right=0.14, second=1240)
    shutil.copyfile(ROOT.parent / 'skin.asterhome' / 'media' / 'aster-icon-128.png',
                    ROOT / 'icon.png')


if __name__ == '__main__':
    main()
