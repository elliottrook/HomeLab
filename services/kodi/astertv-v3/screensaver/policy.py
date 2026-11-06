"""Pure policy for the AsterTV v3 page-aware idle presentation."""

MEDIA = "media"
MUSIC = "music"
NEUTRAL = "neutral"

MEDIA_WINDOWS = frozenset((10000, 11110, 11121, 11125, 11130))
MUSIC_WINDOWS = frozenset((11113, 11114, 11115, 11116, 11117))
VALID_CONTEXTS = frozenset((MEDIA, MUSIC, NEUTRAL))


def context_for_window(window_id):
    try:
        value = int(window_id)
    except (TypeError, ValueError):
        return NEUTRAL
    if value in MUSIC_WINDOWS:
        return MUSIC
    if value in MEDIA_WINDOWS:
        return MEDIA
    return NEUTRAL


def context_for_launch(explicit, window_id):
    """Prefer a reviewed page signal; fail closed for unknown values."""
    value = (explicit or "").strip().casefold()
    if value in VALID_CONTEXTS:
        return value
    if value:
        return NEUTRAL
    return context_for_window(window_id)


def mark_position(step):
    """Move the mark between safe corners to reduce static-pixel exposure."""
    positions = ((1630, 878), (50, 878), (1630, 48), (50, 48))
    return positions[int(step) % len(positions)]

