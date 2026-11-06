# AsterTV v3 News player candidate

This is a presentation-only v3 candidate. It maps the accepted digest player's
existing story, timing, image and ownership properties into an AsterTV player
that keeps the active story visible. It does not alter the digest feed,
narration, audio cache, ownership fencing or production deployment.

The large artwork follows `Digest.Image`. The story rail uses each entry's
existing published image and automatically follows the active row already
selected by `DigestPlayer.tick()`. Gold denotes the active-but-unfocused story;
jade denotes remote focus. The whole-digest progress bar uses Kodi's player
progress and the existing Previous, Play/Pause, Next, Stop and Back actions.

`transform.py` performs the one required controller adaptation: it exposes the
already loaded story image and source on each list item. The transform is exact
and fail-closed. Production installation belongs to a later fleet composition
and is deliberately absent here.
