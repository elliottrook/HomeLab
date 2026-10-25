#!/usr/bin/env python3
"""Build Aster's original, softly enveloped air-puff UI sounds."""

from __future__ import annotations

import math
import random
import shutil
import struct
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RATE = 48_000


def click(path: Path, *, frequency: float, duration: float = 0.080,
          left: float = 0.15, right: float = 0.15) -> None:
    """Write a low-pass noise puff without a sharp attack or pitched oscillator.

    Keep the old call signature so the established directional gains remain
    explicit. ``frequency`` now sets the noise filter, not a musical pitch.
    """
    rng = random.Random('horizontal' if path.name in ('nav-left.wav', 'nav-right.wav') else path.name)
    frames = []
    count = round(RATE * duration)
    filtered = 0.0
    filtered_again = 0.0
    alpha = 1.0 - math.exp(-2.0 * math.pi * frequency / RATE)
    for index in range(count):
        t = index / RATE
        filtered += alpha * (rng.uniform(-1.0, 1.0) - filtered)
        filtered_again += alpha * (filtered - filtered_again)
        attack = math.sin(min(1.0, t / 0.014) * math.pi / 2.0) ** 2
        tail = math.sin(min(1.0, (count - 1 - index) / (RATE * 0.035))
                        * math.pi / 2.0) ** 2
        sample = filtered_again * attack * tail * math.exp(-20.0 * t) * 2.0
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
    # Vertical motion uses a subtle timbre cue, never a pitched tone.
    click(resources / 'nav-up.wav', frequency=1160, left=0.13, right=0.13)
    click(resources / 'nav-down.wav', frequency=760, left=0.13, right=0.13)
    click(resources / 'select.wav', frequency=680, duration=0.090,
          left=0.17, right=0.17)
    click(resources / 'back.wav', frequency=620, duration=0.090,
          left=0.13, right=0.13)
    click(resources / 'notify.wav', frequency=820, duration=0.095,
          left=0.14, right=0.14)
    shutil.copyfile(ROOT.parent / 'skin.asterhome' / 'media' / 'aster-icon-128.png',
                    ROOT / 'icon.png')


if __name__ == '__main__':
    main()
